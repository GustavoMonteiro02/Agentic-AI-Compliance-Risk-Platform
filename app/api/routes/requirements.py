from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.schemas.requirements import RequirementRead
from app.services.requirement_service import RequirementService

router = APIRouter(prefix="/requirements", tags=["requirements"])


@router.get("")
def list_requirements(db: DbSession, q: str | None = Query(default=None)) -> list[RequirementRead]:
    service = RequirementService(db)
    records = service.search(q) if q else service.list()
    return [RequirementRead.model_validate(record) for record in records]
