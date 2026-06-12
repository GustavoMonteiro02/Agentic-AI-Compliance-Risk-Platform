from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi import Query

from app.api.deps import DbSession
from app.api.pagination import PaginationParams, get_pagination, paginate
from app.schemas.risk_register import (
    PolicyExceptionCreate,
    PolicyExceptionQueueItem,
    PolicyExceptionRead,
    PolicyExceptionUpdate,
    RiskRegisterItemRead,
    RiskRegisterItemUpdate,
)
from app.security import AuthenticatedUser, require_roles
from app.services.risk_register_service import PolicyExceptionService, RiskRegisterService

router = APIRouter(prefix="/risk-register", tags=["risk-register"], dependencies=[Depends(require_roles("viewer"))])


@router.get("")
def list_risks(
    response: Response,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("viewer"))],
    pagination: PaginationParams = Depends(get_pagination),
) -> list[RiskRegisterItemRead]:
    risks = [RiskRegisterItemRead.model_validate(item) for item in RiskRegisterService(db, user.tenant_id).list()]
    return paginate(risks, pagination, response)


@router.post("/assessments/{assessment_id}/sync")
def sync_assessment_risks(
    assessment_id: str,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
) -> list[RiskRegisterItemRead]:
    return [
        RiskRegisterItemRead.model_validate(item)
        for item in RiskRegisterService(db, user.tenant_id).sync_from_assessment(assessment_id, user)
    ]


@router.patch("/{item_id}")
def update_risk(
    item_id: str,
    payload: RiskRegisterItemUpdate,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
) -> RiskRegisterItemRead:
    return RiskRegisterItemRead.model_validate(RiskRegisterService(db, user.tenant_id).update(item_id, payload, user))


@router.get("/exceptions")
def list_exceptions(
    response: Response,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("viewer"))],
    pagination: PaginationParams = Depends(get_pagination),
) -> list[PolicyExceptionRead]:
    exceptions = [
        PolicyExceptionRead.model_validate(item)
        for item in PolicyExceptionService(db, user.tenant_id).list()
    ]
    return paginate(exceptions, pagination, response)


@router.get("/exceptions/expiring")
def expiring_exceptions(
    response: Response,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("viewer"))],
    within_days: int = Query(default=30, ge=0, le=365),
    include_expired: bool = Query(default=True),
    pagination: PaginationParams = Depends(get_pagination),
) -> list[PolicyExceptionQueueItem]:
    queue = PolicyExceptionService(db, user.tenant_id).expiring(
        within_days=within_days,
        include_expired=include_expired,
    )
    return paginate(queue, pagination, response)


@router.post("/exceptions/expire-due")
def expire_due_exceptions(
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
) -> list[PolicyExceptionRead]:
    return [
        PolicyExceptionRead.model_validate(item)
        for item in PolicyExceptionService(db, user.tenant_id).expire_due(user)
    ]


@router.post("/exceptions")
def create_exception(
    payload: PolicyExceptionCreate,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
) -> PolicyExceptionRead:
    return PolicyExceptionRead.model_validate(PolicyExceptionService(db, user.tenant_id).create(payload, user))


@router.patch("/exceptions/{exception_id}")
def update_exception(
    exception_id: str,
    payload: PolicyExceptionUpdate,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
) -> PolicyExceptionRead:
    return PolicyExceptionRead.model_validate(
        PolicyExceptionService(db, user.tenant_id).update(exception_id, payload, user)
    )
