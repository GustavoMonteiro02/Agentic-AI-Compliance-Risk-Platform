from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_system_and_assessment():
    system_response = client.post(
        "/systems",
        json={
            "name": "Recruitment CV Screening Assistant",
            "description": (
                "We use an AI assistant in HR to analyze CVs, rank candidates and generate "
                "recommendations for recruiters. The system processes personal data."
            ),
            "business_unit": "People Operations",
        },
    )
    assert system_response.status_code == 200

    system_id = system_response.json()["id"]
    assessment_response = client.post(f"/systems/{system_id}/assess")

    assert assessment_response.status_code == 200
    assessment = assessment_response.json()
    assert assessment["risk_classification"]["risk_level"] == "high"
    assert assessment["status"] == "needs_review"
    assert assessment["retrieved_requirements"]


def test_report_exports_markdown():
    system_response = client.post(
        "/systems",
        json={
            "name": "Report Export System",
            "description": "AI assistant in HR analyzes CVs and recommends candidates to recruiters.",
        },
    )
    assessment = client.post(f"/systems/{system_response.json()['id']}/assess").json()

    report_response = client.get(f"/reports/{assessment['id']}")
    card_response = client.get(f"/reports/{assessment['id']}/system-card")

    assert report_response.status_code == 200
    assert "# Audit Readiness Report" in report_response.text
    assert card_response.status_code == 200
    assert "# AI System Card" in card_response.text
