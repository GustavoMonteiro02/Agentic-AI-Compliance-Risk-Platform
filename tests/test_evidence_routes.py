from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def _create_assessment() -> dict:
    system = client.post(
        "/systems",
        json={
            "name": "Evidence Workflow System",
            "description": "AI assistant in HR analyzes CVs and recommends candidates to recruiters.",
        },
    ).json()
    return client.post(f"/systems/{system['id']}/assess").json()


def test_evidence_items_can_be_listed_and_updated():
    assessment = _create_assessment()
    evidence_response = client.get(f"/evidence/assessments/{assessment['id']}")

    assert evidence_response.status_code == 200
    evidence_items = evidence_response.json()
    assert evidence_items

    item = evidence_items[0]
    update_response = client.patch(
        f"/evidence/items/{item['id']}",
        json={"status": "uploaded", "description": "Uploaded draft evidence."},
    )

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "uploaded"
    assert update_response.json()["description"] == "Uploaded draft evidence."
    assert update_response.json()["due_date"]
    audit_events = client.get(f"/audit/assessments/{assessment['id']}/events").json()
    assert audit_events[0]["action"] == "evidence.updated"
    assert audit_events[0]["details_json"]["previous_status"] == item["status"]


def test_readiness_score_reflects_evidence_updates():
    assessment = _create_assessment()
    initial = client.get(f"/evidence/assessments/{assessment['id']}/readiness-score").json()
    evidence_items = client.get(f"/evidence/assessments/{assessment['id']}").json()

    for item in evidence_items[:3]:
        client.patch(f"/evidence/items/{item['id']}", json={"status": "approved"})

    updated = client.get(f"/evidence/assessments/{assessment['id']}/readiness-score").json()

    assert updated["score"] > initial["score"]
    assert updated["approved"] == 3


def test_readiness_tracks_approval_and_expiry():
    assessment = _create_assessment()
    item = client.get(f"/evidence/assessments/{assessment['id']}").json()[0]
    expired_at = (datetime.utcnow() - timedelta(days=1)).isoformat()

    approved = client.patch(
        f"/evidence/items/{item['id']}",
        json={
            "status": "approved",
            "approved_by": "Compliance Lead",
            "review_notes": "Reviewed against source evidence.",
            "expires_at": expired_at,
        },
    ).json()

    readiness = client.get(f"/evidence/assessments/{assessment['id']}/readiness-score").json()

    assert approved["approved_by"] == "Compliance Lead"
    assert approved["approved_at"]
    assert approved["review_notes"] == "Reviewed against source evidence."
    assert readiness["expired"] >= 1
