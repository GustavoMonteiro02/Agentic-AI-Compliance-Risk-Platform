from fastapi import APIRouter, Query, Response
from sqlalchemy import text

from app.config import get_settings
from app.database.migrations import migration_status
from app.database.session import SessionLocal
from app.database.session import engine as database_engine
from app.llm.provider import OptionalLLMProvider
from app.observability.metrics import http_metrics
from app.prompts.registry import PROMPT_REGISTRY
from app.rag.ingest import legal_source_summary
from app.rag.retriever import LocalComplianceRetriever
from app.rag.vector_store import PineconeVectorStore, QdrantVectorStore

router = APIRouter(prefix="/runtime", tags=["runtime"])


@router.get("/status")
def runtime_status() -> dict:
    settings = get_settings()
    return {
        "ai_generation_mode": settings.ai_generation_mode,
        "llm_enabled": OptionalLLMProvider().enabled(),
        "llm_provider": settings.llm_provider,
        "openai_model": settings.openai_model,
        "openai_base_url": settings.openai_base_url if settings.ai_generation_mode == "openai" else None,
        "anthropic_model": settings.anthropic_model if settings.llm_provider == "anthropic" else None,
        "anthropic_base_url": settings.anthropic_base_url if settings.llm_provider == "anthropic" else None,
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
        "platform_api_key_configured": bool(settings.platform_api_key or settings.platform_api_key_sha256),
        "platform_api_key_hash_configured": bool(settings.platform_api_key_sha256),
        "cors_allowed_origins": settings.cors_origins,
        "security_headers_enabled": settings.security_headers_enabled,
        "security_hsts_enabled": settings.security_hsts_enabled,
        "max_request_body_bytes": settings.max_request_body_bytes,
        "api_rate_limit_per_minute": settings.api_rate_limit_per_minute,
        "review_policy": {
            "sla_hours": settings.review_sla_hours,
            "missing_evidence_escalation_threshold": settings.review_missing_evidence_escalation_threshold,
            "high_risk_critical_gap_escalation": settings.review_high_risk_critical_gap_escalation,
        },
        "notification_delivery": {
            "mode": settings.notification_delivery_mode,
            "webhook_configured": bool(settings.notification_webhook_url),
            "webhook_timeout_seconds": settings.notification_webhook_timeout_seconds,
        },
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

    try:
        legal_sources = legal_source_summary(settings.knowledge_base_path)
        sources = legal_sources.get("sources", [])
        available = [source for source in sources if source.get("available")]
        complete = [source for source in sources if source.get("ingestion_status") == "available" and source.get("available")]
        checks["legal_sources"] = {
            "ok": bool(available),
            "manifest": legal_sources.get("manifest"),
            "source_count": len(sources),
            "available_count": len(available),
            "complete_count": len(complete),
            "ready_for_full_legal_corpus": bool(legal_sources.get("validation", {}).get("ready")),
            "validation": legal_sources.get("validation", {}),
        }
    except Exception as exc:
        checks["legal_sources"] = {"ok": False, "error": str(exc)}

    checks["auth"] = {
        "ok": settings.auth_mode == "disabled" or bool(settings.platform_api_key or settings.platform_api_key_sha256),
        "mode": settings.auth_mode,
        "tenant": settings.default_tenant_id,
        "api_key_configured": bool(settings.platform_api_key or settings.platform_api_key_sha256),
        "api_key_hash_configured": bool(settings.platform_api_key_sha256),
    }
    try:
        checks["database_migrations"] = migration_status(database_engine)
    except Exception as exc:
        checks["database_migrations"] = {"ok": False, "current": False, "error": str(exc)}
    checks["api_hardening"] = {
        "ok": settings.max_request_body_bytes > 0 and settings.security_headers_enabled,
        "security_headers_enabled": settings.security_headers_enabled,
        "hsts_enabled": settings.security_hsts_enabled,
        "max_request_body_bytes": settings.max_request_body_bytes,
        "rate_limit_per_minute": settings.api_rate_limit_per_minute,
    }
    checks["llm"] = {
        "ok": settings.ai_generation_mode not in {"openai", "llm"}
        or (
            bool(settings.openai_api_key)
            if settings.llm_provider in {"openai", "openai_compatible"}
            else bool(settings.anthropic_api_key)
            if settings.llm_provider == "anthropic"
            else False
        ),
        "mode": settings.ai_generation_mode,
        "provider": settings.llm_provider,
        "model": settings.anthropic_model if settings.llm_provider == "anthropic" else settings.openai_model,
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


@router.get("/preflight")
def runtime_preflight(target: str = Query(default="production", pattern="^(production|staging|development)$")) -> dict:
    settings = get_settings()
    readiness = runtime_readiness()
    checks = readiness["checks"]
    blockers: list[dict] = []
    warnings: list[dict] = []
    actions: list[str] = []

    def add_blocker(code: str, message: str, action: str, check: str | None = None) -> None:
        blockers.append({"code": code, "message": message, "check": check})
        actions.append(action)

    def add_warning(code: str, message: str, action: str, check: str | None = None) -> None:
        warnings.append({"code": code, "message": message, "check": check})
        actions.append(action)

    for check_name, check in checks.items():
        if check.get("ok") is False or check.get("current") is False:
            add_blocker(
                f"{check_name}_not_ready",
                check.get("error") or f"{check_name.replace('_', ' ')} check is not ready.",
                f"Fix {check_name.replace('_', ' ')} before release.",
                check_name,
            )

    legal_check = checks.get("legal_sources", {})
    if not legal_check.get("ready_for_full_legal_corpus"):
        add_warning(
            "legal_corpus_partial",
            "Legal-source corpus is not marked ready for full official-source use.",
            "Load official article-level legal sources and run make validate-legal-sources.",
            "legal_sources",
        )

    if target in {"production", "staging"} and settings.auth_mode == "disabled":
        add_warning(
            "auth_disabled",
            "API authentication is disabled.",
            "Set AUTH_MODE=api_key and configure PLATFORM_API_KEY before shared environments.",
            "auth",
        )
    if target == "production" and not settings.security_hsts_enabled:
        add_warning(
            "hsts_disabled",
            "HSTS is disabled.",
            "Enable SECURITY_HSTS_ENABLED=true once the API is served exclusively over HTTPS.",
            "api_hardening",
        )
    if target == "production" and settings.api_rate_limit_per_minute <= 0:
        add_warning(
            "rate_limit_disabled",
            "API rate limiting is disabled.",
            "Set API_RATE_LIMIT_PER_MINUTE to a tenant-appropriate production value.",
            "api_hardening",
        )
    if target == "production" and settings.vector_db == "local":
        add_warning(
            "local_vector_store",
            "Vector search is using the local fallback.",
            "Set VECTOR_DB=qdrant or VECTOR_DB=pinecone and ingest the corpus for persistent retrieval.",
            "vector_db",
        )
    if target == "production" and settings.ai_generation_mode == "deterministic":
        add_warning(
            "llm_disabled",
            "LLM refinement is disabled; outputs use deterministic generation only.",
            "Set AI_GENERATION_MODE=llm and configure an LLM provider if production requires live LLM refinement.",
            "llm",
        )
    if settings.notification_delivery_mode == "webhook" and not settings.notification_webhook_url:
        add_warning(
            "notification_webhook_missing",
            "Webhook notification delivery is enabled without a default webhook URL.",
            "Set NOTIFICATION_WEBHOOK_URL or ensure every webhook event has a recipient URL.",
            "notification_delivery",
        )

    unique_actions = list(dict.fromkeys(actions))
    release_ready = not blockers and (target == "development" or not warnings)
    return {
        "target": target,
        "release_ready": release_ready,
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "blockers": blockers,
        "warnings": warnings,
        "actions": unique_actions,
        "checks": checks,
    }


@router.get("/metrics")
def runtime_metrics() -> dict:
    return http_metrics.snapshot()


@router.get("/metrics.prom")
def runtime_metrics_prometheus() -> Response:
    return Response(content=http_metrics.prometheus(), media_type="text/plain; version=0.0.4")
