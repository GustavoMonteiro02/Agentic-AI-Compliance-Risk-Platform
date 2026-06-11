from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import DbSession
from app.api.pagination import PaginationParams, get_pagination, paginate
from app.schemas.incidents import IncidentCreate, IncidentRead, IncidentUpdate
from app.security import AuthenticatedUser, require_roles
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/incidents", tags=["incidents"], dependencies=[Depends(require_roles("viewer"))])


@router.get("")
def list_incidents(
    response: Response,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("viewer"))],
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    pagination: PaginationParams = Depends(get_pagination),
) -> list[IncidentRead]:
    service = IncidentService(db, user.tenant_id)
    incidents = [IncidentRead.model_validate(item) for item in service.list(status=status, severity=severity)]
    return paginate(incidents, pagination, response)


@router.post("")
def create_incident(
    payload: IncidentCreate,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
) -> IncidentRead:
    return IncidentRead.model_validate(IncidentService(db, user.tenant_id).create(payload, user))


@router.patch("/{incident_id}")
def update_incident(
    incident_id: str,
    payload: IncidentUpdate,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
) -> IncidentRead:
    return IncidentRead.model_validate(IncidentService(db, user.tenant_id).update(incident_id, payload, user))
