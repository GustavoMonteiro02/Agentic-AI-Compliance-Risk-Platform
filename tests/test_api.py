from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["kind"] == "liveness"


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


def test_report_exports_pdf():
    system_response = client.post(
        "/systems",
        json={
            "name": "PDF Export System",
            "description": "AI assistant in HR analyzes CVs and recommends candidates to recruiters.",
        },
    )
    assessment = client.post(f"/systems/{system_response.json()['id']}/assess").json()

    report_response = client.get(f"/reports/{assessment['id']}.pdf")
    card_response = client.get(f"/reports/{assessment['id']}/system-card.pdf")

    assert report_response.status_code == 200
    assert report_response.headers["content-type"] == "application/pdf"
    assert report_response.content.startswith(b"%PDF")
    assert card_response.status_code == 200
    assert card_response.content.startswith(b"%PDF")


def test_assessment_remediation_plan_prioritizes_gaps_and_evidence():
    system_response = client.post(
        "/systems",
        json={
            "name": "Remediation Planning System",
            "description": "AI assistant in HR analyzes CVs and recommends candidates to recruiters.",
        },
    )
    assessment = client.post(f"/systems/{system_response.json()['id']}/assess").json()

    response = client.get(f"/assessments/{assessment['id']}/remediation-plan")

    assert response.status_code == 200
    plan = response.json()
    assert plan["assessment_id"] == assessment["id"]
    assert plan["actions"]
    assert plan["overall_priority"] in {"critical", "high", "medium", "low"}
    assert any(action["source"] == "missing_evidence" for action in plan["actions"])
    assert plan["critical_gap_count"] == len(assessment["gap_analysis"]["critical_gaps"])
