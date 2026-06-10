from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession
from app.schemas.audit import AuditEventRead
from app.security import AuthenticatedUser, require_roles
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"], dependencies=[Depends(require_roles("auditor"))])


@router.get("/assessments/{assessment_id}/events")
def assessment_events(
    assessment_id: str,
    db: DbSession,
    _user: Annotated[AuthenticatedUser, Depends(require_roles("auditor"))],
) -> list[AuditEventRead]:
    return [AuditEventRead.model_validate(event) for event in AuditService(db).list_for_assessment(assessment_id)]
