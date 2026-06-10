from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import DbSession
from app.schemas.system import AISystemCreate
from app.security import require_roles
from app.services.assessment_service import AssessmentService
from app.services.demo_service import DemoScenarioService
from app.services.system_service import SystemService

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/scenarios")
def list_demo_scenarios() -> list[dict]:
    return DemoScenarioService().list()


@router.post("/scenarios/{slug}/assess", dependencies=[Depends(require_roles("compliance_reviewer"))])
def create_and_assess_demo_scenario(slug: str, db: DbSession) -> dict:
    try:
        payload = DemoScenarioService().get(slug)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Demo scenario not found") from None
    system = SystemService(db).create(AISystemCreate(**payload))
    return AssessmentService(db).assess_system(system.id).model_dump(mode="json")
