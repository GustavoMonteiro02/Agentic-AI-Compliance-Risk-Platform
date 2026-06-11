from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession
from app.rag.retriever import LocalComplianceRetriever, RetrievalFilters
from app.schemas.requirements import RequirementRead, RequirementSearchResult
from app.security import require_roles
from app.services.requirement_service import RequirementService

router = APIRouter(prefix="/requirements", tags=["requirements"], dependencies=[Depends(require_roles("viewer"))])


@router.get("")
def list_requirements(db: DbSession, q: str | None = Query(default=None)) -> list[RequirementRead]:
    service = RequirementService(db)
    records = service.search(q) if q else service.list()
    return [RequirementRead.model_validate(record) for record in records]


@router.get("/search")
def search_requirements(
    q: str = Query(min_length=2),
    top_k: int = Query(default=6, ge=1, le=20),
    jurisdiction: str | None = Query(default=None),
    document_type: str | None = Query(default=None),
    category: str | None = Query(default=None),
    tags: list[str] | None = Query(default=None),
    authority: str | None = Query(default=None),
) -> list[RequirementSearchResult]:
    filters = RetrievalFilters.from_values(
        jurisdiction=jurisdiction,
        document_type=document_type,
        category=category,
        tags=tags,
        authority=authority,
    )
    results = LocalComplianceRetriever().search(q, top_k=top_k, filters=filters)
    return [RequirementSearchResult.model_validate(result) for result in results]
