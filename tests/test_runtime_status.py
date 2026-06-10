from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_runtime_status_reports_production_toggles():
    response = client.get("/runtime/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ai_generation_mode"] == "deterministic"
    assert payload["llm_enabled"] is False
    assert payload["vector_db"] == "local"
    assert payload["prompt_versions"]["llm_refiner"] == "2026-06-10.v1"
