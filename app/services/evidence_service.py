from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import models
from app.schemas.evidence import EvidenceUpdate
from app.security import AuthenticatedUser
from app.services.audit_service import AuditService


class EvidenceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_assessment(self, assessment_id: str) -> list[models.EvidenceItemRecord]:
        return list(
            self.db.scalars(
                select(models.EvidenceItemRecord)
                .where(models.EvidenceItemRecord.assessment_id == assessment_id)
                .order_by(models.EvidenceItemRecord.priority, models.EvidenceItemRecord.name)
            )
        )

    def update(
        self,
        evidence_id: str,
        payload: EvidenceUpdate,
        user: AuthenticatedUser | None = None,
    ) -> models.EvidenceItemRecord:
        record = self.db.get(models.EvidenceItemRecord, evidence_id)
        if not record:
            raise HTTPException(status_code=404, detail="Evidence item not found")
        previous_status = record.status
        record.status = payload.status
        if payload.description is not None:
            record.description = payload.description
        if payload.owner is not None:
            record.owner = payload.owner
        if payload.file_url is not None:
            record.file_url = payload.file_url
        if payload.due_date is not None:
            record.due_date = payload.due_date
        if payload.expires_at is not None:
            record.expires_at = payload.expires_at
        if payload.review_notes is not None:
            record.review_notes = payload.review_notes
        if payload.approved_by is not None:
            record.approved_by = payload.approved_by
        if payload.status == "approved" and record.approved_at is None:
            record.approved_at = datetime.utcnow()
        if payload.status != "approved":
            record.approved_at = None
        self.db.commit()
        self.db.refresh(record)
        if user:
            AuditService(self.db).record(
                user=user,
                action="evidence.updated",
                resource_type="evidence_item",
                resource_id=record.id,
                assessment_id=record.assessment_id,
                details={
                    "name": record.name,
                    "previous_status": previous_status,
                    "status": record.status,
                    "owner": record.owner,
                    "file_url_present": bool(record.file_url),
                },
            )
        return record

    def readiness_score(self, assessment_id: str) -> dict:
        items = self.list_for_assessment(assessment_id)
        if not items:
            return {"assessment_id": assessment_id, "score": 0.0, "approved": 0, "total": 0, "overdue": 0, "expired": 0}

        now = datetime.utcnow()
        weights = {"missing": 0.0, "rejected": 0.0, "partial": 0.35, "generated": 0.55, "uploaded": 0.75, "approved": 1.0}
        expired_items = {item.id for item in items if item.expires_at and item.expires_at < now}
        weighted_sum = 0.0
        for item in items:
            item_score = weights.get(item.status, 0.0)
            if item.id in expired_items:
                item_score = min(item_score, 0.35)
            weighted_sum += item_score
        score = round(weighted_sum / len(items) * 100, 1)
        return {
            "assessment_id": assessment_id,
            "score": score,
            "approved": sum(1 for item in items if item.status == "approved"),
            "total": len(items),
            "missing": sum(1 for item in items if item.status == "missing"),
            "overdue": sum(1 for item in items if item.status not in {"approved", "rejected"} and item.due_date and item.due_date < now),
            "expired": len(expired_items),
        }
