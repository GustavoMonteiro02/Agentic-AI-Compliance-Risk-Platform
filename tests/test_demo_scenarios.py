from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_demo_scenarios_can_be_listed_and_assessed():
    response = client.get("/demo/scenarios")

    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) >= 4
    assert any(item["slug"] == "recruitment_cv_screening" for item in scenarios)

    assessment_response = client.post("/demo/scenarios/recruitment_cv_screening/assess")

    assert assessment_response.status_code == 200
    assessment = assessment_response.json()
    assert assessment["risk_classification"]["risk_level"] == "high"
    assert assessment["status"] == "needs_review"

