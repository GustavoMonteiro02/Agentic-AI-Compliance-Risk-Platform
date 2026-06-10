from fastapi import APIRouter, Depends

from app.api.deps import DbSession
from app.schemas.assessment import AssessmentRunRequest
from app.schemas.system import AISystemCreate, AISystemUpdate
from app.security import require_roles
from app.services.assessment_service import AssessmentService
from app.services.system_service import SystemService

router = APIRouter(prefix="/systems", tags=["systems"], dependencies=[Depends(require_roles("viewer"))])


def serialize_system(system) -> dict:
    metadata = system.system_metadata or {}
    return {
        "id": system.id,
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
def create_system(payload: AISystemCreate, db: DbSession) -> dict:
    return serialize_system(SystemService(db).create(payload))


@router.get("")
def list_systems(db: DbSession) -> list[dict]:
    return [serialize_system(system) for system in SystemService(db).list()]


@router.get("/{system_id}")
def get_system(system_id: str, db: DbSession) -> dict:
    return serialize_system(SystemService(db).get(system_id))


@router.put("/{system_id}", dependencies=[Depends(require_roles("admin"))])
def update_system(system_id: str, payload: AISystemUpdate, db: DbSession) -> dict:
    return serialize_system(SystemService(db).update(system_id, payload))


@router.post("/{system_id}/intake", dependencies=[Depends(require_roles("compliance_reviewer"))])
def intake_system(system_id: str, db: DbSession, payload: AssessmentRunRequest | None = None) -> dict:
    return AssessmentService(db).assess_system(system_id, payload).model_dump(mode="json")["profile"]


@router.post("/{system_id}/assess", dependencies=[Depends(require_roles("compliance_reviewer"))])
def assess_system(system_id: str, db: DbSession, payload: AssessmentRunRequest | None = None) -> dict:
    return AssessmentService(db).assess_system(system_id, payload).model_dump(mode="json")


@router.get("/{system_id}/assessment")
def latest_assessment(system_id: str, db: DbSession) -> dict:
    return AssessmentService(db).latest_for_system(system_id).model_dump(mode="json")
