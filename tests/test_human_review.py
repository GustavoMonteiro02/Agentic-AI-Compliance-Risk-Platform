from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_human_review_approval_requires_notes():
    system = client.post(
        "/systems",
        json={
            "name": "Review Guardrail System",
            "description": "AI assistant in HR analyzes CVs and recommends candidates to recruiters.",
        },
    ).json()
    assessment = client.post(f"/systems/{system['id']}/assess").json()

    response = client.post(
        f"/reviews/{assessment['id']}/approve",
        json={"reviewer": "Compliance Reviewer", "notes": ""},
    )

    assert response.status_code == 400


def test_human_review_can_approve_with_notes():
    system = client.post(
        "/systems",
        json={
            "name": "Approval Workflow System",
            "description": "AI assistant in HR analyzes CVs and recommends candidates to recruiters.",
        },
    ).json()
    assessment = client.post(f"/systems/{system['id']}/assess").json()

    response = client.post(
        f"/reviews/{assessment['id']}/approve",
        json={"reviewer": "Compliance Reviewer", "notes": "Approved after review of evidence plan."},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"

