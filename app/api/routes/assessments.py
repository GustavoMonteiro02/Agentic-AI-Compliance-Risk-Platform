from fastapi import APIRouter

from app.api.deps import DbSession
from app.services.assessment_service import AssessmentService

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("")
def list_assessments(db: DbSession) -> list[dict]:
    return [item.model_dump(mode="json") for item in AssessmentService(db).list()]


@router.get("/{assessment_id}")
def get_assessment(assessment_id: str, db: DbSession) -> dict:
    return AssessmentService(db).get(assessment_id).model_dump(mode="json")


@router.post("/{assessment_id}/risk-classification")
def risk_classification(assessment_id: str, db: DbSession) -> dict:
    return AssessmentService(db).get(assessment_id).risk_classification.model_dump()


@router.post("/{assessment_id}/gap-analysis")
def gap_analysis(assessment_id: str, db: DbSession) -> dict:
    return AssessmentService(db).get(assessment_id).gap_analysis.model_dump()


@router.post("/{assessment_id}/evidence-checklist")
def evidence_checklist(assessment_id: str, db: DbSession) -> list[dict]:
    return [item.model_dump() for item in AssessmentService(db).get(assessment_id).evidence_checklist]


@router.post("/{assessment_id}/system-card")
def system_card(assessment_id: str, db: DbSession) -> dict:
    return AssessmentService(db).get(assessment_id).ai_system_card.model_dump()


@router.post("/{assessment_id}/audit-report")
def audit_report(assessment_id: str, db: DbSession) -> dict:
    return AssessmentService(db).get(assessment_id).audit_report.model_dump()


@router.get("/{assessment_id}/tool-calls")
def tool_calls(assessment_id: str, db: DbSession) -> list[dict]:
    return AssessmentService(db).get(assessment_id).tool_calls


@router.get("/{assessment_id}/evidence")
def evidence(assessment_id: str, db: DbSession) -> list[dict]:
    return [item.model_dump() for item in AssessmentService(db).get(assessment_id).evidence_checklist]

