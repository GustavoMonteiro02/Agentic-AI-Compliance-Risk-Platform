from fastapi import APIRouter
from sqlalchemy import text

from app.config import get_settings
from app.database.session import SessionLocal
from app.llm.provider import OptionalLLMProvider
from app.prompts.registry import PROMPT_REGISTRY
from app.rag.retriever import LocalComplianceRetriever
from app.rag.vector_store import PineconeVectorStore, QdrantVectorStore

router = APIRouter(prefix="/runtime", tags=["runtime"])


@router.get("/status")
def runtime_status() -> dict:
    settings = get_settings()
    return {
        "ai_generation_mode": settings.ai_generation_mode,
        "llm_enabled": OptionalLLMProvider().enabled(),
        "openai_model": settings.openai_model,
        "openai_base_url": settings.openai_base_url if settings.ai_generation_mode == "openai" else None,
        "openai_timeout_seconds": settings.openai_timeout_seconds,
        "openai_max_retries": settings.openai_max_retries,
        "langsmith_tracing": settings.langsmith_tracing,
        "langsmith_project": settings.langsmith_project,
        "langsmith_api_url": settings.langsmith_api_url,
        "vector_db": settings.vector_db,
        "qdrant_url": settings.qdrant_url if settings.vector_db == "qdrant" else None,
        "pinecone_index_host": settings.pinecone_index_host if settings.vector_db == "pinecone" else None,
        "pinecone_namespace": settings.pinecone_namespace if settings.vector_db == "pinecone" else None,
        "embedding_provider": settings.embedding_provider,
        "embedding_model": settings.openai_embedding_model if settings.embedding_provider == "openai" else "local_hash",
        "prompt_versions": {name: prompt.version for name, prompt in PROMPT_REGISTRY.items()},
        "auth_mode": settings.auth_mode,
        "default_user_role": settings.default_user_role,
        "default_tenant_id": settings.default_tenant_id,
    }


@router.get("/readiness")
def runtime_readiness() -> dict:
    settings = get_settings()
    checks: dict[str, dict] = {}

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = {"ok": True}
    except Exception as exc:
        checks["database"] = {"ok": False, "error": str(exc)}

    try:
        chunk_count = len(LocalComplianceRetriever().load())
        checks["knowledge_base"] = {"ok": chunk_count > 0, "chunk_count": chunk_count}
    except Exception as exc:
        checks["knowledge_base"] = {"ok": False, "error": str(exc)}

    checks["auth"] = {
        "ok": settings.auth_mode == "disabled" or bool(settings.platform_api_key),
        "mode": settings.auth_mode,
        "tenant": settings.default_tenant_id,
    }
    checks["llm"] = {
        "ok": settings.ai_generation_mode != "openai" or bool(settings.openai_api_key),
        "mode": settings.ai_generation_mode,
        "model": settings.openai_model,
        "timeout_seconds": settings.openai_timeout_seconds,
        "max_retries": settings.openai_max_retries,
    }
    checks["embeddings"] = {
        "ok": settings.embedding_provider != "openai" or bool(settings.openai_api_key),
        "provider": settings.embedding_provider,
        "model": settings.openai_embedding_model if settings.embedding_provider == "openai" else "local_hash",
        "dimensions": settings.embedding_dimensions,
    }
    checks["langsmith"] = {
        "ok": not settings.langsmith_tracing or bool(settings.langsmith_api_key),
        "tracing": settings.langsmith_tracing,
        "project": settings.langsmith_project,
        "api_url": settings.langsmith_api_url,
    }

    if settings.vector_db == "qdrant":
        try:
            health = QdrantVectorStore(settings.qdrant_url, settings.qdrant_collection).health()
            checks["vector_db"] = {"ok": bool(health.get("available")), **health}
        except Exception as exc:
            checks["vector_db"] = {"ok": False, "error": str(exc)}
    elif settings.vector_db == "pinecone":
        if not settings.pinecone_api_key or not settings.pinecone_index_host:
            checks["vector_db"] = {
                "ok": False,
                "mode": "pinecone",
                "error": "PINECONE_API_KEY and PINECONE_INDEX_HOST are required",
            }
        else:
            try:
                health = PineconeVectorStore(
                    settings.pinecone_api_key,
                    settings.pinecone_index_host,
                    settings.pinecone_namespace,
                ).health()
                checks["vector_db"] = {"ok": bool(health.get("available")), "mode": "pinecone", **health}
            except Exception as exc:
                checks["vector_db"] = {"ok": False, "mode": "pinecone", "error": str(exc)}
    else:
        checks["vector_db"] = {"ok": True, "mode": "local"}

    ready = all(item.get("ok") for item in checks.values())
    return {"ready": ready, "checks": checks}
