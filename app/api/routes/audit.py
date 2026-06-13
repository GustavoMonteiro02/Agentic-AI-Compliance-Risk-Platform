from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import Response as FastAPIResponse

from app.api.deps import DbSession
from app.api.pagination import PaginationParams, get_pagination, paginate
from app.schemas.audit import AuditEventRead
from app.security import AuthenticatedUser, require_roles
from app.services.audit_package_service import AuditPackageService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"], dependencies=[Depends(require_roles("auditor"))])


@router.get("/tenant/export")
def tenant_audit_export(
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("auditor"))],
) -> dict:
    return AuditPackageService(db, user.tenant_id).build_tenant_export()


@router.get("/tenant/export.zip")
def tenant_audit_export_zip(
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("auditor"))],
) -> FastAPIResponse:
    content = AuditPackageService(db, user.tenant_id).build_tenant_export_zip()
    return FastAPIResponse(
        content=content,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{user.tenant_id}_audit_export.zip"'},
    )


@router.get("/events")
def tenant_events(
    response: Response,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("auditor"))],
    limit: int = Query(default=100, ge=1, le=250),
    pagination: PaginationParams = Depends(get_pagination),
) -> list[AuditEventRead]:
    events = [
        AuditEventRead.model_validate(event)
        for event in AuditService(db).list_for_tenant(user.tenant_id, limit=limit)
    ]
    return paginate(events, pagination, response)


@router.get("/assessments/{assessment_id}/events")
def assessment_events(
    assessment_id: str,
    response: Response,
    db: DbSession,
    _user: Annotated[AuthenticatedUser, Depends(require_roles("auditor"))],
    pagination: PaginationParams = Depends(get_pagination),
) -> list[AuditEventRead]:
    events = [
        AuditEventRead.model_validate(event)
        for event in AuditService(db).list_for_assessment(assessment_id, _user.tenant_id)
    ]
    return paginate(events, pagination, response)


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
) -> FastAPIResponse:
    content = AuditPackageService(db, user.tenant_id).build_zip(assessment_id)
    return FastAPIResponse(
        content=content,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{assessment_id}_audit_package.zip"'},
    )
