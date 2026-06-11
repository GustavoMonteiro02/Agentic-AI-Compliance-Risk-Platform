from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.api.deps import DbSession
from app.schemas.audit import AuditEventRead
from app.security import AuthenticatedUser, require_roles
from app.services.audit_package_service import AuditPackageService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"], dependencies=[Depends(require_roles("auditor"))])


@router.get("/assessments/{assessment_id}/events")
def assessment_events(
    assessment_id: str,
    db: DbSession,
    _user: Annotated[AuthenticatedUser, Depends(require_roles("auditor"))],
) -> list[AuditEventRead]:
    return [
        AuditEventRead.model_validate(event)
        for event in AuditService(db).list_for_assessment(assessment_id, _user.tenant_id)
    ]


@router.get("/assessments/{assessment_id}/package")
def assessment_audit_package(
    assessment_id: str,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("auditor"))],
) -> dict:
    return AuditPackageService(db, user.tenant_id).build(assessment_id)


@router.get("/assessments/{assessment_id}/package.zip")
def assessment_audit_package_zip(
    assessment_id: str,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("auditor"))],
) -> Response:
    content = AuditPackageService(db, user.tenant_id).build_zip(assessment_id)
    return Response(
        content=content,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{assessment_id}_audit_package.zip"'},
    )
