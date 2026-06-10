from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession
from app.schemas.evidence import EvidenceRecordRead, EvidenceUpdate
from app.security import AuthenticatedUser, require_roles
from app.services.evidence_service import EvidenceService

router = APIRouter(prefix="/evidence", tags=["evidence"], dependencies=[Depends(require_roles("viewer"))])


@router.get("/assessments/{assessment_id}")
def list_evidence(
    assessment_id: str,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("viewer"))],
) -> list[EvidenceRecordRead]:
    return [
        EvidenceRecordRead.model_validate(item)
        for item in EvidenceService(db, user.tenant_id).list_for_assessment(assessment_id)
    ]


@router.patch("/items/{evidence_id}", dependencies=[Depends(require_roles("compliance_reviewer"))])
def update_evidence(
    evidence_id: str,
    payload: EvidenceUpdate,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
) -> EvidenceRecordRead:
    return EvidenceRecordRead.model_validate(EvidenceService(db, user.tenant_id).update(evidence_id, payload, user))


@router.get("/assessments/{assessment_id}/readiness-score")
def readiness_score(
    assessment_id: str,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("viewer"))],
) -> dict:
    return EvidenceService(db, user.tenant_id).readiness_score(assessment_id)
