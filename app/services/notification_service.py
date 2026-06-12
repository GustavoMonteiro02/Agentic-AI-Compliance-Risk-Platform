from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import models
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
