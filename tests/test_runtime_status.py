from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.api.main import create_app
from app.api.main import app
from app.observability.metrics import http_metrics


client = TestClient(app)


def test_settings_ignore_frontend_only_environment_keys(monkeypatch):
    monkeypatch.setenv("API_BASE_URL", "http://127.0.0.1:8000")
    monkeypatch.setenv("PLATFORM_USER", "streamlit-user")
    monkeypatch.setenv("PLATFORM_USER_ROLE", "admin")
    monkeypatch.setenv("PLATFORM_TENANT_ID", "default")

    settings = Settings()

    assert settings.app_name == "AI Governance & Compliance Intelligence Platform"


def test_runtime_status_reports_production_toggles():
    response = client.get("/runtime/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ai_generation_mode"] == "deterministic"
    assert payload["llm_enabled"] is False
    assert payload["llm_provider"] == "openai"
    assert payload["vector_db"] == "local"
    assert payload["embedding_provider"] == "local_hash"
    assert payload["langsmith_api_url"] == "https://api.smith.langchain.com"
    assert payload["prompt_versions"]["llm_refiner"] == "2026-06-10.v1"
    assert payload["auth_mode"] == "disabled"
    assert payload["platform_api_key_configured"] is False
    assert payload["platform_api_key_hash_configured"] is False
    assert payload["cors_allowed_origins"] == []
    assert payload["security_headers_enabled"] is True
    assert payload["security_hsts_enabled"] is False
    assert payload["max_request_body_bytes"] == 1_048_576
    assert payload["api_rate_limit_per_minute"] == 0
    assert payload["review_policy"] == {
        "sla_hours": 48,
        "missing_evidence_escalation_threshold": 3,
        "high_risk_critical_gap_escalation": True,
    }
    assert payload["notification_delivery"] == {
        "mode": "manual",
        "webhook_configured": False,
        "webhook_timeout_seconds": 10,
    }


def test_runtime_llm_options_only_lists_configured_providers(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    get_settings.cache_clear()
    try:
        test_client = TestClient(create_app())
        response = test_client.get("/runtime/llm-options")
    finally:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        get_settings.cache_clear()

    assert response.status_code == 200
    payload = response.json()
    assert [provider["id"] for provider in payload["providers"]] == ["openai"]
    assert payload["default_provider"] == "openai"
    assert payload["defaults"]["max_tokens"] == 2000


def test_runtime_llm_options_lists_openai_compatible_for_custom_base_url(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "ollama")
    monkeypatch.setenv("OPENAI_BASE_URL", "http://ollama:11434/v1")
    monkeypatch.setenv("OPENAI_MODEL", "llama3.2:3b")
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    get_settings.cache_clear()
    try:
        test_client = TestClient(create_app())
        response = test_client.get("/runtime/llm-options")
    finally:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        get_settings.cache_clear()

    assert response.status_code == 200
    payload = response.json()
    assert [provider["id"] for provider in payload["providers"]] == ["openai_compatible"]
    assert payload["providers"][0]["model"] == "llama3.2:3b"
    assert payload["providers"][0]["base_url"] == "http://ollama:11434/v1"
    assert payload["default_provider"] == "openai_compatible"


def test_runtime_readiness_reports_operational_checks():
    response = client.get("/runtime/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ready"] is True
    assert payload["checks"]["database"]["ok"] is True
    assert payload["checks"]["knowledge_base"]["chunk_count"] > 0
    assert payload["checks"]["legal_sources"]["available_count"] >= 1
    assert payload["checks"]["legal_sources"]["ready_for_full_legal_corpus"] is False
    assert payload["checks"]["langsmith"]["ok"] is True
    assert payload["checks"]["embeddings"]["provider"] == "local_hash"
    assert payload["checks"]["vector_db"]["ok"] is True
    assert payload["checks"]["database_migrations"]["current"] is True
    assert payload["checks"]["api_hardening"]["security_headers_enabled"] is True
    assert payload["checks"]["api_hardening"]["max_request_body_bytes"] == 1_048_576
    assert payload["checks"]["auth"]["api_key_configured"] is False
    assert payload["checks"]["auth"]["api_key_hash_configured"] is False


def test_runtime_preflight_reports_production_warnings():
    response = client.get("/runtime/preflight")

    assert response.status_code == 200
    payload = response.json()
    warning_codes = {item["code"] for item in payload["warnings"]}
    assert payload["target"] == "production"
    assert payload["release_ready"] is False
    assert payload["blocker_count"] == 0
    assert {"auth_disabled", "legal_corpus_partial", "local_vector_store", "rate_limit_disabled"} <= warning_codes
    assert any("AUTH_MODE=api_key" in action for action in payload["actions"])
    assert "checks" in payload


def test_runtime_preflight_development_allows_warnings_without_blocking():
    response = client.get("/runtime/preflight?target=development")

    assert response.status_code == 200
    payload = response.json()
    assert payload["target"] == "development"
    assert payload["release_ready"] is True
    assert payload["warning_count"] >= 1


def test_runtime_readiness_reports_missing_pinecone_credentials(monkeypatch):
    monkeypatch.setenv("VECTOR_DB", "pinecone")
    monkeypatch.delenv("PINECONE_API_KEY", raising=False)
    monkeypatch.delenv("PINECONE_INDEX_HOST", raising=False)
    get_settings.cache_clear()
    try:
        response = client.get("/runtime/readiness")
    finally:
        monkeypatch.delenv("VECTOR_DB", raising=False)
        get_settings.cache_clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["ready"] is False
    assert payload["checks"]["vector_db"]["mode"] == "pinecone"
    assert "PINECONE_API_KEY" in payload["checks"]["vector_db"]["error"]


def test_cors_preflight_is_enabled_for_configured_origins(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://console.example.com")
    get_settings.cache_clear()
    try:
        test_client = TestClient(create_app())
    finally:
        monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
        get_settings.cache_clear()

    response = test_client.options(
        "/health",
        headers={
            "Origin": "https://console.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://console.example.com"


def test_security_headers_are_enabled_by_default():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"
    assert response.headers["cache-control"] == "no-store"
    assert "x-response-time-ms" in response.headers


def test_runtime_metrics_report_request_counts():
    http_metrics.reset()

    health_response = client.get("/health")
    metrics_response = client.get("/runtime/metrics")
    prometheus_response = client.get("/runtime/metrics.prom")

    assert health_response.status_code == 200
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()
    assert metrics["total_requests"] >= 1
    assert metrics["routes"]["GET /health"]["request_count"] == 1
    assert prometheus_response.status_code == 200
    assert "ai_governance_http_requests_total" in prometheus_response.text
    assert 'route="/health"' in prometheus_response.text


def test_request_size_limit_rejects_large_payloads(monkeypatch):
    monkeypatch.setenv("MAX_REQUEST_BODY_BYTES", "8")
    get_settings.cache_clear()
    try:
        test_client = TestClient(create_app())
    finally:
        monkeypatch.delenv("MAX_REQUEST_BODY_BYTES", raising=False)
        get_settings.cache_clear()

    response = test_client.post("/systems", json={"name": "oversized"})

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "request_too_large"


def test_rate_limit_rejects_excess_requests(monkeypatch):
    monkeypatch.setenv("API_RATE_LIMIT_PER_MINUTE", "1")
    get_settings.cache_clear()
    try:
        test_client = TestClient(create_app())
    finally:
        monkeypatch.delenv("API_RATE_LIMIT_PER_MINUTE", raising=False)
        get_settings.cache_clear()

    first = test_client.get("/runtime/status", headers={"X-Tenant-ID": "tenant-a", "X-User": "limited-user"})
    second = test_client.get("/runtime/status", headers={"X-Tenant-ID": "tenant-a", "X-User": "limited-user"})

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers["ratelimit-limit"] == "1"
    assert second.json()["error"]["code"] == "rate_limit_exceeded"
