from __future__ import annotations

from datetime import datetime
from urllib.parse import urlparse

from fastapi import HTTPException
import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import models
from app.schemas.notifications import NotificationDispatchResult, NotificationEventUpdate
from app.schemas.review import ReviewQueueItem
from app.security import AuthenticatedUser
from app.services.audit_service import AuditService


class NotificationService:
    def __init__(self, db: Session, tenant_id: str = "default") -> None:
        self.db = db
        self.tenant_id = tenant_id

    def list(
        self,
        *,
        status: str | None = None,
        event_type: str | None = None,
    ) -> list[models.NotificationEvent]:
        statement = select(models.NotificationEvent).where(models.NotificationEvent.tenant_id == self.tenant_id)
        if status:
            statement = statement.where(models.NotificationEvent.status == status)
        if event_type:
            statement = statement.where(models.NotificationEvent.event_type == event_type)
        return list(self.db.scalars(statement.order_by(models.NotificationEvent.created_at.desc())))

    def update(
        self,
        notification_id: str,
        payload: NotificationEventUpdate,
        user: AuthenticatedUser | None = None,
    ) -> models.NotificationEvent:
        event = self.db.scalar(
            select(models.NotificationEvent)
            .where(
                models.NotificationEvent.id == notification_id,
                models.NotificationEvent.tenant_id == self.tenant_id,
            )
            .limit(1)
        )
        if not event:
            raise HTTPException(status_code=404, detail="Notification event not found")

        previous_status = event.status
        event.status = payload.status
        event.payload_json = {
            **(event.payload_json or {}),
            **({"delivery_notes": payload.delivery_notes} if payload.delivery_notes else {}),
        }
        if payload.status == "delivered" and event.delivered_at is None:
            event.delivered_at = datetime.utcnow()
        if payload.status in {"queued", "failed", "skipped"}:
            event.delivered_at = None

        self.db.commit()
        self.db.refresh(event)

        if user:
            AuditService(self.db).record(
                user=user,
                action=f"notification.{payload.status}",
                resource_type="notification_event",
                resource_id=event.id,
                assessment_id=event.assessment_id,
                details={
                    "previous_status": previous_status,
                    "status": event.status,
                    "event_type": event.event_type,
                    "channel": event.channel,
                    "recipient": event.recipient,
                },
            )
        return event

    def dispatch_queued(
        self,
        *,
        event_type: str | None = None,
        limit: int = 25,
        user: AuthenticatedUser | None = None,
    ) -> list[NotificationDispatchResult]:
        settings = get_settings()
        statement = (
            select(models.NotificationEvent)
            .where(
                models.NotificationEvent.tenant_id == self.tenant_id,
                models.NotificationEvent.status == "queued",
            )
        )
        if event_type:
            statement = statement.where(models.NotificationEvent.event_type == event_type)
        statement = statement.order_by(models.NotificationEvent.created_at.asc()).limit(limit)
        events = list(self.db.scalars(statement))
        results = [self._dispatch_event(event, settings) for event in events]
        self.db.commit()
        for event in events:
            self.db.refresh(event)

        if user and results:
            AuditService(self.db).record(
                user=user,
                action="notification.dispatch_queued",
                resource_type="notification_event",
                details={
                    "count": len(results),
                    "delivered": sum(1 for item in results if item.status == "delivered"),
                    "failed": sum(1 for item in results if item.status == "failed"),
                    "skipped": sum(1 for item in results if item.status == "skipped"),
                    "event_type": event_type,
                },
            )
        return results

    def _dispatch_event(self, event: models.NotificationEvent, settings: object) -> NotificationDispatchResult:
        if settings.notification_delivery_mode != "webhook":
            event.status = "skipped"
            event.payload_json = {
                **(event.payload_json or {}),
                "delivery_notes": "Notification delivery mode is manual.",
                "dispatched_at": datetime.utcnow().isoformat(),
            }
            return NotificationDispatchResult(
                notification_id=event.id,
                status=event.status,
                channel=event.channel,
                recipient=event.recipient,
                detail="Notification delivery mode is manual.",
            )

        target_url = event.recipient if event.channel == "webhook" and event.recipient else settings.notification_webhook_url
        if not _valid_webhook_url(target_url):
            event.status = "failed"
            event.payload_json = {
                **(event.payload_json or {}),
                "delivery_notes": "Missing or invalid HTTPS webhook URL.",
                "dispatched_at": datetime.utcnow().isoformat(),
            }
            return NotificationDispatchResult(
                notification_id=event.id,
                status=event.status,
                channel=event.channel,
                recipient=event.recipient,
                detail="Missing or invalid HTTPS webhook URL.",
            )

        payload = {
            "id": event.id,
            "tenant_id": event.tenant_id,
            "assessment_id": event.assessment_id,
            "event_type": event.event_type,
            "subject": event.subject,
            "message": event.message,
            "payload": event.payload_json or {},
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }
        try:
            response = requests.post(
                target_url,
                json=payload,
                timeout=settings.notification_webhook_timeout_seconds,
            )
            http_status = response.status_code
            response.raise_for_status()
            event.status = "delivered"
            event.delivered_at = datetime.utcnow()
            detail = "Webhook delivered."
        except requests.RequestException as exc:
            http_status = getattr(getattr(exc, "response", None), "status_code", None)
            event.status = "failed"
            detail = f"Webhook delivery failed: {exc}"

        event.payload_json = {
            **(event.payload_json or {}),
            "delivery_notes": detail,
            "delivery_http_status": http_status,
            "dispatched_at": datetime.utcnow().isoformat(),
        }
        return NotificationDispatchResult(
            notification_id=event.id,
            status=event.status,
            channel=event.channel,
            recipient=event.recipient,
            detail=detail,
            http_status=http_status,
        )

    def queue_review_escalations(
        self,
        escalations: list[ReviewQueueItem],
        *,
        recipient: str | None = None,
        channel: str = "in_app",
        user: AuthenticatedUser | None = None,
    ) -> list[models.NotificationEvent]:
        queued: list[models.NotificationEvent] = []
        for escalation in escalations:
            dedupe_key = f"review_escalation:{self.tenant_id}:{escalation.assessment_id}:{escalation.escalation_level}"
            existing = self.db.scalar(
                select(models.NotificationEvent)
                .where(
                    models.NotificationEvent.tenant_id == self.tenant_id,
                    models.NotificationEvent.dedupe_key == dedupe_key,
                )
                .limit(1)
            )
            if existing:
                queued.append(existing)
                continue

            event = models.NotificationEvent(
                tenant_id=self.tenant_id,
                assessment_id=escalation.assessment_id,
                event_type="review_escalation",
                channel=channel,
                recipient=recipient,
                subject=f"{escalation.escalation_level.upper()} review escalation: {escalation.system_name}",
                message=escalation.escalation_reason
                or f"{escalation.system_name} has been waiting {escalation.age_hours}h for review.",
                status="queued",
                dedupe_key=dedupe_key,
                payload_json=escalation.model_dump(mode="json"),
                created_at=datetime.utcnow(),
            )
            self.db.add(event)
            queued.append(event)

        self.db.commit()
        for event in queued:
            self.db.refresh(event)

        if user and queued:
            AuditService(self.db).record(
                user=user,
                action="notification.review_escalations_queued",
                resource_type="notification_event",
                assessment_id=None,
                details={
                    "count": len(queued),
                    "event_ids": [event.id for event in queued],
                    "channel": channel,
                    "recipient": recipient,
                },
            )
        return queued


def _valid_webhook_url(url: str | None) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.scheme == "https" and bool(parsed.netloc)
