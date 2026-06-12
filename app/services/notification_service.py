from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import models
from app.schemas.notifications import NotificationEventUpdate
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
