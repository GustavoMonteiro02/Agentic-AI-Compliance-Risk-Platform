import hashlib

from fastapi.testclient import TestClient

from app.api.main import app
from app.config import get_settings


client = TestClient(app)


def _enable_api_key_auth(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "api_key")
    monkeypatch.setenv("PLATFORM_API_KEY", "test-secret")
    monkeypatch.setenv("DEFAULT_USER_ROLE", "viewer")
    get_settings.cache_clear()


def test_api_key_auth_rejects_missing_key(monkeypatch):
    _enable_api_key_auth(monkeypatch)

    response = client.get("/systems")

    get_settings.cache_clear()
    assert response.status_code == 401
    payload = response.json()
    assert payload["detail"] == "Invalid or missing API key"
    assert payload["error"]["code"] == "unauthorized"
    assert payload["request_id"] == response.headers["x-request-id"]


def test_viewer_can_read_but_not_create_systems(monkeypatch):
    _enable_api_key_auth(monkeypatch)
    headers = {"X-API-Key": "test-secret", "X-User-Role": "viewer"}

    read_response = client.get("/systems", headers=headers)
    write_response = client.post(
        "/systems",
        headers=headers,
        json={"name": "Blocked", "description": "Should not be created."},
    )

    get_settings.cache_clear()
    assert read_response.status_code == 200
    assert write_response.status_code == 403


def test_admin_can_create_system_with_api_key(monkeypatch):
    _enable_api_key_auth(monkeypatch)

    response = client.post(
        "/systems",
        headers={"X-API-Key": "test-secret", "X-User-Role": "admin", "X-User": "platform-admin"},
        json={"name": "RBAC System", "description": "System created through admin role."},
    )

    get_settings.cache_clear()
    assert response.status_code == 200
    assert response.json()["name"] == "RBAC System"


def test_api_key_auth_accepts_sha256_configured_key(monkeypatch):
    secret_hash = hashlib.sha256(b"hashed-secret").hexdigest()
    monkeypatch.setenv("AUTH_MODE", "api_key")
    monkeypatch.delenv("PLATFORM_API_KEY", raising=False)
    monkeypatch.setenv("PLATFORM_API_KEY_SHA256", secret_hash)
    monkeypatch.setenv("DEFAULT_USER_ROLE", "viewer")
    get_settings.cache_clear()
    try:
        accepted = client.get("/systems", headers={"Authorization": "Bearer hashed-secret"})
        rejected = client.get("/systems", headers={"Authorization": "Bearer wrong-secret"})
    finally:
        monkeypatch.delenv("AUTH_MODE", raising=False)
        monkeypatch.delenv("PLATFORM_API_KEY_SHA256", raising=False)
        monkeypatch.delenv("DEFAULT_USER_ROLE", raising=False)
        get_settings.cache_clear()

    assert accepted.status_code == 200
    assert rejected.status_code == 401
