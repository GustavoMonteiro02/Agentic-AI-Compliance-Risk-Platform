from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import models
from app.security import AuthenticatedUser


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        *,
        user: AuthenticatedUser,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        assessment_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> models.AuditEvent:
        event = models.AuditEvent(
            tenant_id=user.tenant_id,
            assessment_id=assessment_id,
            actor=user.subject,
            actor_role=user.role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details_json=details or {},
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list_for_assessment(self, assessment_id: str, tenant_id: str = "default") -> list[models.AuditEvent]:
        return list(
            self.db.scalars(
                select(models.AuditEvent)
                .where(
                    models.AuditEvent.assessment_id == assessment_id,
                    models.AuditEvent.tenant_id == tenant_id,
                )
                .order_by(models.AuditEvent.created_at.desc())
            )
        )

    def list_for_tenant(self, tenant_id: str = "default", limit: int = 100) -> list[models.AuditEvent]:
        return list(
            self.db.scalars(
                select(models.AuditEvent)
                .where(models.AuditEvent.tenant_id == tenant_id)
                .order_by(models.AuditEvent.created_at.desc())
                .limit(limit)
            )
        )
