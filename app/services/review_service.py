from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database import models
from app.database.repositories import AssessmentRepository
from app.schemas.review import ReviewDecision, ReviewRead


class ReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.assessments = AssessmentRepository(db)

    def decide(self, assessment_id: str, status: str, payload: ReviewDecision) -> ReviewRead:
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
        return ReviewRead(assessment_id=assessment_id, reviewer=payload.reviewer, status=status, notes=notes)

