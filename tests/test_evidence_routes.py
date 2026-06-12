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
    collected_at = datetime.utcnow().isoformat()
    update_response = client.patch(
        f"/evidence/items/{item['id']}",
        json={
            "status": "uploaded",
            "description": "Uploaded draft evidence.",
            "file_url": "s3://audit-evidence/hr-bias-report.pdf",
            "source_system": "GRC evidence vault",
            "evidence_hash": "sha256:abc123",
            "collected_at": collected_at,
            "evidence_metadata_json": {"control_id": "HUMAN_OVERSIGHT_001", "collector": "qa-analyst"},
        },
    )

    payload = update_response.json()
    assert update_response.status_code == 200
    assert payload["status"] == "uploaded"
    assert payload["description"] == "Uploaded draft evidence."
    assert payload["file_url"] == "s3://audit-evidence/hr-bias-report.pdf"
    assert payload["source_system"] == "GRC evidence vault"
    assert payload["evidence_hash"] == "sha256:abc123"
    assert payload["evidence_metadata_json"]["collector"] == "qa-analyst"
    assert payload["due_date"]
    audit_events = client.get(f"/audit/assessments/{assessment['id']}/events").json()
    assert audit_events[0]["action"] == "evidence.updated"
    assert audit_events[0]["details_json"]["previous_status"] == item["status"]
    assert audit_events[0]["details_json"]["source_system"] == "GRC evidence vault"
    assert audit_events[0]["details_json"]["evidence_hash_present"] is True


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
    retention_until = (datetime.utcnow() - timedelta(days=2)).isoformat()

    approved = client.patch(
        f"/evidence/items/{item['id']}",
        json={
            "status": "approved",
            "approved_by": "Compliance Lead",
            "review_notes": "Reviewed against source evidence.",
            "expires_at": expired_at,
            "retention_until": retention_until,
        },
    ).json()

    readiness = client.get(f"/evidence/assessments/{assessment['id']}/readiness-score").json()

    assert approved["approved_by"] == "Compliance Lead"
    assert approved["approved_at"]
    assert approved["review_notes"] == "Reviewed against source evidence."
    assert readiness["expired"] >= 1
    assert readiness["retention_due"] >= 1
