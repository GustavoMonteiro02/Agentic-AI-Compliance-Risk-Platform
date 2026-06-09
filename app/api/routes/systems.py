from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.assessment import AssessmentRunRequest
from app.schemas.system import AISystemCreate, AISystemUpdate
from app.services.assessment_service import AssessmentService
from app.services.system_service import SystemService

router = APIRouter(prefix="/systems", tags=["systems"])


def serialize_system(system) -> dict:
    return {
        "id": system.id,
        "name": system.name,
        "description": system.description,
        "business_unit": system.business_unit,
        "owner": system.owner,
        "technical_owner": system.technical_owner,
        "deployment_status": system.deployment_status,
        "users_affected": system.users_affected,
        "data_types": system.data_types,
        "model_provider": system.model_provider,
        "model_type": system.model_type,
        "decision_impact": system.decision_impact,
        "autonomy_level": system.autonomy_level,
        "human_oversight_process": system.human_oversight_process,
        "metadata": system.system_metadata,
        "created_at": system.created_at,
        "updated_at": system.updated_at,
    }


@router.post("")
def create_system(payload: AISystemCreate, db: DbSession) -> dict:
    return serialize_system(SystemService(db).create(payload))


@router.get("")
def list_systems(db: DbSession) -> list[dict]:
    return [serialize_system(system) for system in SystemService(db).list()]


@router.get("/{system_id}")
def get_system(system_id: str, db: DbSession) -> dict:
    return serialize_system(SystemService(db).get(system_id))


@router.put("/{system_id}")
def update_system(system_id: str, payload: AISystemUpdate, db: DbSession) -> dict:
    return serialize_system(SystemService(db).update(system_id, payload))


@router.post("/{system_id}/intake")
def intake_system(system_id: str, db: DbSession, payload: AssessmentRunRequest | None = None) -> dict:
    return AssessmentService(db).assess_system(system_id, payload).model_dump(mode="json")["profile"]


@router.post("/{system_id}/assess")
def assess_system(system_id: str, db: DbSession, payload: AssessmentRunRequest | None = None) -> dict:
    return AssessmentService(db).assess_system(system_id, payload).model_dump(mode="json")


@router.get("/{system_id}/assessment")
def latest_assessment(system_id: str, db: DbSession) -> dict:
    return AssessmentService(db).latest_for_system(system_id).model_dump(mode="json")
