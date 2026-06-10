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
    audit_events = client.get(f"/audit/assessments/{assessment['id']}/events").json()
    assert audit_events[0]["action"] == "review.approved"
    assert audit_events[0]["actor"] == "local-dev"


def test_review_queue_and_history_are_available():
    system = client.post(
        "/systems",
        json={
            "name": "Queue Workflow System",
            "description": "AI assistant in HR analyzes CVs and recommends candidates to recruiters.",
        },
    ).json()
    assessment = client.post(f"/systems/{system['id']}/assess").json()

    queue_response = client.get("/reviews/queue")
    queue_ids = {item["assessment_id"] for item in queue_response.json()}
    assert assessment["id"] in queue_ids

    client.post(
        f"/reviews/{assessment['id']}/request-more-evidence",
        json={"reviewer": "Compliance Reviewer", "notes": "Need evaluation report."},
    )
    history = client.get(f"/reviews/{assessment['id']}/history").json()

    assert history[0]["status"] == "needs_more_evidence"
    assert history[0]["reviewer"] == "Compliance Reviewer"
