from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import models
from app.database.repositories import AssessmentRepository
from app.schemas.review import ReviewDecision, ReviewQueueItem, ReviewRead
from app.security import AuthenticatedUser
from app.services.audit_service import AuditService


class ReviewService:
    def __init__(self, db: Session, tenant_id: str = "default") -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.assessments = AssessmentRepository(db, tenant_id)

    def decide(
        self,
        assessment_id: str,
        status: str,
        payload: ReviewDecision,
        user: AuthenticatedUser | None = None,
    ) -> ReviewRead:
        assessment = self.assessments.get(assessment_id)
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        if status == "approved" and not payload.notes.strip():
            raise HTTPException(status_code=400, detail="Approval requires reviewer notes")
        if payload.override_risk_level and not payload.override_justification:
            raise HTTPException(status_code=400, detail="Risk override requires justification")

        notes = payload.notes
        if payload.override_risk_level:
            notes = f"{notes}\nRisk override: {payload.override_risk_level}. {payload.override_justification}"
            data = dict(assessment.assessment_json)
            data["risk_classification"]["risk_level"] = payload.override_risk_level
            assessment.assessment_json = data
            assessment.risk_level = payload.override_risk_level

        self.assessments.update_status(assessment, status, notes)
        review = models.HumanReview(
            assessment_id=assessment_id,
            reviewer=payload.reviewer,
            status=status,
            notes=notes,
        )
        self.db.add(review)
        self.db.commit()
        if user:
            AuditService(self.db).record(
                user=user,
                action=f"review.{status}",
                resource_type="human_review",
                resource_id=review.id,
                assessment_id=assessment_id,
                details={
                    "reviewer": payload.reviewer,
                    "status": status,
                    "override_risk_level": payload.override_risk_level,
                    "notes_present": bool(notes.strip()),
                },
            )
        return ReviewRead(assessment_id=assessment_id, reviewer=payload.reviewer, status=status, notes=notes)

    def queue(self, statuses: list[str] | None = None) -> list[ReviewQueueItem]:
        selected_statuses = statuses or ["needs_review", "needs_more_evidence"]
        records = self.assessments.list_by_status(selected_statuses)
        items: list[ReviewQueueItem] = []
        for record in records:
            data = record.assessment_json
            items.append(
                ReviewQueueItem(
                    assessment_id=record.id,
                    system_id=record.system_id,
                    system_name=data["profile"]["system_name"],
                    risk_level=data["risk_classification"]["risk_level"],
                    status=record.status,
                    critical_gap_count=len(data["gap_analysis"]["critical_gaps"]),
                    missing_evidence_count=sum(
                        1 for item in data["evidence_checklist"] if item["status"] == "missing"
                    ),
                )
            )
        return items

    def history(self, assessment_id: str) -> list[ReviewRead]:
        if not self.assessments.get(assessment_id):
            raise HTTPException(status_code=404, detail="Assessment not found")
        reviews = self.db.scalars(
            select(models.HumanReview)
            .where(models.HumanReview.assessment_id == assessment_id)
            .order_by(models.HumanReview.created_at.desc())
        )
        return [
            ReviewRead(
                assessment_id=review.assessment_id,
                reviewer=review.reviewer,
                status=review.status,
                notes=review.notes,
            )
            for review in reviews
        ]
