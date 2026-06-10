from fastapi import APIRouter, Depends

from app.api.deps import DbSession
from app.schemas.evidence import EvidenceRecordRead, EvidenceUpdate
from app.security import require_roles
from app.services.evidence_service import EvidenceService

router = APIRouter(prefix="/evidence", tags=["evidence"], dependencies=[Depends(require_roles("viewer"))])


@router.get("/assessments/{assessment_id}")
def list_evidence(assessment_id: str, db: DbSession) -> list[EvidenceRecordRead]:
    return [
        EvidenceRecordRead.model_validate(item)
        for item in EvidenceService(db).list_for_assessment(assessment_id)
    ]


@router.patch("/items/{evidence_id}", dependencies=[Depends(require_roles("compliance_reviewer"))])
def update_evidence(evidence_id: str, payload: EvidenceUpdate, db: DbSession) -> EvidenceRecordRead:
    return EvidenceRecordRead.model_validate(EvidenceService(db).update(evidence_id, payload))


@router.get("/assessments/{assessment_id}/readiness-score")
def readiness_score(assessment_id: str, db: DbSession) -> dict:
    return EvidenceService(db).readiness_score(assessment_id)
