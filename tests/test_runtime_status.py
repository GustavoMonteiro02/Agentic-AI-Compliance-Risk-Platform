from fastapi.testclient import TestClient

from app.config import get_settings
from app.api.main import create_app
from app.api.main import app


client = TestClient(app)


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
    assert payload["cors_allowed_origins"] == []
    assert payload["security_headers_enabled"] is True
    assert payload["security_hsts_enabled"] is False
    assert payload["max_request_body_bytes"] == 1_048_576
    assert payload["api_rate_limit_per_minute"] == 0


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
    assert payload["checks"]["api_hardening"]["security_headers_enabled"] is True
    assert payload["checks"]["api_hardening"]["max_request_body_bytes"] == 1_048_576


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
