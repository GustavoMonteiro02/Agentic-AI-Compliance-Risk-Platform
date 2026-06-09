from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import models
from app.schemas.evidence import EvidenceUpdate


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

    def update(self, evidence_id: str, payload: EvidenceUpdate) -> models.EvidenceItemRecord:
        record = self.db.get(models.EvidenceItemRecord, evidence_id)
        if not record:
            raise HTTPException(status_code=404, detail="Evidence item not found")
        record.status = payload.status
        if payload.description is not None:
            record.description = payload.description
        if payload.owner is not None:
            record.owner = payload.owner
        if payload.file_url is not None:
            record.file_url = payload.file_url
        self.db.commit()
        self.db.refresh(record)
        return record

    def readiness_score(self, assessment_id: str) -> dict:
        items = self.list_for_assessment(assessment_id)
        if not items:
            return {"assessment_id": assessment_id, "score": 0.0, "approved": 0, "total": 0}

        weights = {"missing": 0.0, "rejected": 0.0, "partial": 0.35, "generated": 0.55, "uploaded": 0.75, "approved": 1.0}
        score = round(sum(weights.get(item.status, 0.0) for item in items) / len(items) * 100, 1)
        return {
            "assessment_id": assessment_id,
            "score": score,
            "approved": sum(1 for item in items if item.status == "approved"),
            "total": len(items),
            "missing": sum(1 for item in items if item.status == "missing"),
        }

