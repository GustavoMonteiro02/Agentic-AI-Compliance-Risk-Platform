from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import DbSession
from app.api.pagination import PaginationParams, get_pagination, paginate
from app.config import get_settings
from app.rag.ingest import legal_source_summary
from app.rag.retriever import LocalComplianceRetriever, RetrievalFilters
from app.schemas.requirements import RequirementRead, RequirementSearchResult
from app.security import require_roles
from app.services.requirement_service import RequirementService

router = APIRouter(prefix="/requirements", tags=["requirements"], dependencies=[Depends(require_roles("viewer"))])


@router.get("")
def list_requirements(
    response: Response,
    db: DbSession,
    q: str | None = Query(default=None),
    pagination: PaginationParams = Depends(get_pagination),
) -> list[RequirementRead]:
    service = RequirementService(db)
    records = service.search(q) if q else service.list()
    requirements = [RequirementRead.model_validate(record) for record in records]
    return paginate(requirements, pagination, response)


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


@router.get("/legal-sources")
def legal_sources() -> dict:
    summary = legal_source_summary(get_settings().knowledge_base_path)
    sources = summary.get("sources", [])
    available = [source for source in sources if source.get("available")]
    complete = [source for source in sources if source.get("ingestion_status") == "available" and source.get("available")]
    return {
        **summary,
        "source_count": len(sources),
        "available_count": len(available),
        "complete_count": len(complete),
        "ready_for_full_legal_corpus": bool(summary.get("validation", {}).get("ready")),
    }
