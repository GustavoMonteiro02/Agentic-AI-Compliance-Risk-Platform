from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import models
from app.database.repositories import AssessmentRepository
from app.config import get_settings
from app.schemas.review import ReviewDecision, ReviewQueueItem, ReviewRead
from app.security import AuthenticatedUser
from app.services.audit_service import AuditService


def _review_escalation(
    *,
    created_at: datetime,
    risk_level: str,
    critical_gap_count: int,
    missing_evidence_count: int,
    sla_hours: int,
    missing_evidence_threshold: int,
    high_risk_critical_gap_escalation: bool,
) -> tuple[str, str | None, float]:
    age_hours = round((datetime.utcnow() - created_at).total_seconds() / 3600, 1)
    if age_hours >= sla_hours:
        return "sla_breach", f"Review age {age_hours}h exceeds {sla_hours}h SLA", age_hours
    if high_risk_critical_gap_escalation and risk_level in {"unacceptable", "high"} and critical_gap_count:
        return "urgent", "High-risk assessment has critical compliance gaps", age_hours
    if missing_evidence_count >= missing_evidence_threshold:
        return "attention", f"Assessment has {missing_evidence_count} missing evidence items", age_hours
    return "normal", None, age_hours


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

    def queue(self, statuses: list[str] | None = None, sla_hours: int | None = None) -> list[ReviewQueueItem]:
        settings = get_settings()
        active_sla_hours = sla_hours or settings.review_sla_hours
        selected_statuses = statuses or ["needs_review", "needs_more_evidence"]
        records = self.assessments.list_by_status(selected_statuses)
        items: list[ReviewQueueItem] = []
        for record in records:
            data = record.assessment_json
            critical_gap_count = len(data["gap_analysis"]["critical_gaps"])
            missing_evidence_count = sum(
                1 for item in data["evidence_checklist"] if item["status"] == "missing"
            )
            escalation_level, escalation_reason, age_hours = _review_escalation(
                created_at=record.created_at,
                risk_level=data["risk_classification"]["risk_level"],
                critical_gap_count=critical_gap_count,
                missing_evidence_count=missing_evidence_count,
                sla_hours=active_sla_hours,
                missing_evidence_threshold=settings.review_missing_evidence_escalation_threshold,
                high_risk_critical_gap_escalation=settings.review_high_risk_critical_gap_escalation,
            )
            items.append(
                ReviewQueueItem(
                    assessment_id=record.id,
                    system_id=record.system_id,
                    system_name=data["profile"]["system_name"],
                    risk_level=data["risk_classification"]["risk_level"],
                    status=record.status,
                    critical_gap_count=critical_gap_count,
                    missing_evidence_count=missing_evidence_count,
                    age_hours=age_hours,
                    escalation_level=escalation_level,
                    escalation_reason=escalation_reason,
                )
            )
        return items

    def escalations(self, sla_hours: int | None = None) -> list[ReviewQueueItem]:
        return [item for item in self.queue(sla_hours=sla_hours) if item.escalation_level != "normal"]

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
