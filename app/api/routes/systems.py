from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.deps import DbSession
from app.api.pagination import PaginationParams, get_pagination, paginate
from app.schemas.assessment import AssessmentRunRequest
from app.schemas.system import AISystemCreate, AISystemUpdate
from app.security import AuthenticatedUser, require_roles
from app.services.assessment_service import AssessmentService
from app.services.audit_service import AuditService
from app.services.system_service import SystemService

router = APIRouter(prefix="/systems", tags=["systems"], dependencies=[Depends(require_roles("viewer"))])


def serialize_system(system) -> dict:
    metadata = system.system_metadata or {}
    return {
        "id": system.id,
        "tenant_id": system.tenant_id,
        "name": system.name,
        "description": system.description,
        "business_unit": system.business_unit,
        "owner": system.owner,
        "technical_owner": system.technical_owner,
        "deployment_status": system.deployment_status,
        "users_affected": system.users_affected,
        "external_users_affected": metadata.get("external_users_affected", False),
        "data_types": system.data_types,
        "model_provider": system.model_provider,
        "model_type": system.model_type,
        "decision_impact": system.decision_impact,
        "autonomy_level": system.autonomy_level,
        "human_oversight_process": system.human_oversight_process,
        "integrations_tools_used": metadata.get("integrations_tools_used", []),
        "monitoring_status": metadata.get("monitoring_status"),
        "evaluation_status": metadata.get("evaluation_status"),
        "security_testing_status": metadata.get("security_testing_status"),
        "metadata": metadata,
        "created_at": system.created_at,
        "updated_at": system.updated_at,
    }


@router.post("", dependencies=[Depends(require_roles("admin"))])
def create_system(
    payload: AISystemCreate,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("admin"))],
) -> dict:
    system = SystemService(db, user.tenant_id).create(payload)
    AuditService(db).record(
        user=user,
        action="system.created",
        resource_type="ai_system",
        resource_id=system.id,
        details={"name": system.name, "business_unit": system.business_unit, "deployment_status": system.deployment_status},
    )
    return serialize_system(system)


@router.get("")
def list_systems(
    response: Response,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("viewer"))],
    pagination: PaginationParams = Depends(get_pagination),
) -> list[dict]:
    systems = [serialize_system(system) for system in SystemService(db, user.tenant_id).list()]
    return paginate(systems, pagination, response)


@router.get("/{system_id}")
def get_system(
    system_id: str,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("viewer"))],
) -> dict:
    return serialize_system(SystemService(db, user.tenant_id).get(system_id))


@router.put("/{system_id}", dependencies=[Depends(require_roles("admin"))])
def update_system(
    system_id: str,
    payload: AISystemUpdate,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("admin"))],
) -> dict:
    system = SystemService(db, user.tenant_id).update(system_id, payload)
    AuditService(db).record(
        user=user,
        action="system.updated",
        resource_type="ai_system",
        resource_id=system.id,
        details={"name": system.name, "deployment_status": system.deployment_status},
    )
    return serialize_system(system)


@router.post("/{system_id}/intake", dependencies=[Depends(require_roles("compliance_reviewer"))])
def intake_system(
    system_id: str,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
    payload: AssessmentRunRequest | None = None,
) -> dict:
    assessment = AssessmentService(db, user.tenant_id).assess_system(system_id, payload)
    AuditService(db).record(
        user=user,
        action="assessment.intake_completed",
        resource_type="assessment",
        resource_id=assessment.id,
        assessment_id=assessment.id,
        details={"system_id": system_id, "system_name": assessment.profile.system_name},
    )
    return assessment.model_dump(mode="json")["profile"]


@router.post("/{system_id}/assess", dependencies=[Depends(require_roles("compliance_reviewer"))])
def assess_system(
    system_id: str,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
    payload: AssessmentRunRequest | None = None,
) -> dict:
    assessment = AssessmentService(db, user.tenant_id).assess_system(system_id, payload)
    AuditService(db).record(
        user=user,
        action="assessment.created",
        resource_type="assessment",
        resource_id=assessment.id,
        assessment_id=assessment.id,
        details={
            "system_id": system_id,
            "system_name": assessment.profile.system_name,
            "risk_level": assessment.risk_classification.risk_level,
            "generation_mode": payload.llm_config.ai_generation_mode if payload and payload.llm_config else None,
        },
    )
    return assessment.model_dump(mode="json")


@router.get("/{system_id}/assessment")
def latest_assessment(
    system_id: str,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("viewer"))],
) -> dict:
    return AssessmentService(db, user.tenant_id).latest_for_system(system_id).model_dump(mode="json")
