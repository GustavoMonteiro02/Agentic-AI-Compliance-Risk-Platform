from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession
from app.schemas.risk_register import (
    PolicyExceptionCreate,
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
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("viewer"))],
) -> list[RiskRegisterItemRead]:
    return [RiskRegisterItemRead.model_validate(item) for item in RiskRegisterService(db, user.tenant_id).list()]


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
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("viewer"))],
) -> list[PolicyExceptionRead]:
    return [
        PolicyExceptionRead.model_validate(item)
        for item in PolicyExceptionService(db, user.tenant_id).list()
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
