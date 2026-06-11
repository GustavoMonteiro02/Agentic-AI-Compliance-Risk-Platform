from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession
from app.security import AuthenticatedUser, require_roles
from app.services.assessment_service import AssessmentService

router = APIRouter(prefix="/assessments", tags=["assessments"], dependencies=[Depends(require_roles("viewer"))])


@router.get("")
def list_assessments(
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("viewer"))],
) -> list[dict]:
    return [item.model_dump(mode="json") for item in AssessmentService(db, user.tenant_id).list()]


@router.get("/{assessment_id}")
def get_assessment(
    assessment_id: str,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("viewer"))],
) -> dict:
    return AssessmentService(db, user.tenant_id).get(assessment_id).model_dump(mode="json")


@router.post("/{assessment_id}/risk-classification", dependencies=[Depends(require_roles("compliance_reviewer"))])
def risk_classification(
    assessment_id: str,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
) -> dict:
    return AssessmentService(db, user.tenant_id).get(assessment_id).risk_classification.model_dump()


@router.post("/{assessment_id}/gap-analysis", dependencies=[Depends(require_roles("compliance_reviewer"))])
def gap_analysis(
    assessment_id: str,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
) -> dict:
    return AssessmentService(db, user.tenant_id).get(assessment_id).gap_analysis.model_dump()


@router.post("/{assessment_id}/evidence-checklist", dependencies=[Depends(require_roles("compliance_reviewer"))])
def evidence_checklist(
    assessment_id: str,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
) -> list[dict]:
    return [item.model_dump() for item in AssessmentService(db, user.tenant_id).get(assessment_id).evidence_checklist]


@router.post("/{assessment_id}/system-card", dependencies=[Depends(require_roles("compliance_reviewer"))])
def system_card(
    assessment_id: str,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
) -> dict:
    return AssessmentService(db, user.tenant_id).get(assessment_id).ai_system_card.model_dump()


@router.post("/{assessment_id}/audit-report", dependencies=[Depends(require_roles("compliance_reviewer"))])
def audit_report(
    assessment_id: str,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
) -> dict:
    return AssessmentService(db, user.tenant_id).get(assessment_id).audit_report.model_dump()


@router.get("/{assessment_id}/remediation-plan")
def remediation_plan(
    assessment_id: str,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("viewer"))],
) -> dict:
    return AssessmentService(db, user.tenant_id).remediation_plan(assessment_id).model_dump(mode="json")


@router.get("/{assessment_id}/tool-calls")
def tool_calls(
    assessment_id: str,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("viewer"))],
) -> list[dict]:
    return AssessmentService(db, user.tenant_id).get(assessment_id).tool_calls


@router.get("/{assessment_id}/evidence")
def evidence(
    assessment_id: str,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("viewer"))],
) -> list[dict]:
    return [item.model_dump() for item in AssessmentService(db, user.tenant_id).get(assessment_id).evidence_checklist]
