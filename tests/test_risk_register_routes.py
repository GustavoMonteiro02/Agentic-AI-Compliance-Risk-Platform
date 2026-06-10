from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def _create_assessment(tenant_id: str = "default") -> dict:
    headers = {"X-Tenant-ID": tenant_id, "X-User-Role": "admin", "X-User": "risk-owner"}
    system = client.post(
        "/systems",
        headers=headers,
        json={
            "name": "Risk Register System",
            "description": "AI assistant in HR analyzes CVs and recommends candidates to recruiters.",
        },
    ).json()
    return client.post(f"/systems/{system['id']}/assess", headers=headers).json()


def test_risk_register_syncs_from_assessment_and_updates_item():
    assessment = _create_assessment()

    risks = client.post(f"/risk-register/assessments/{assessment['id']}/sync").json()
    updated = client.patch(
        f"/risk-register/{risks[0]['id']}",
        json={"status": "mitigating", "owner": "Compliance Lead", "mitigation_plan": "Implement control evidence."},
    ).json()
    listed = client.get("/risk-register").json()

    assert risks
    assert updated["status"] == "mitigating"
    assert listed[0]["tenant_id"] == "default"
    assert any(item["id"] == updated["id"] for item in listed)


def test_policy_exception_lifecycle_and_audit_event():
    assessment = _create_assessment()
    expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()

    created = client.post(
        "/risk-register/exceptions",
        json={
            "assessment_id": assessment["id"],
            "requirement_id": "HUMAN_OVERSIGHT_001",
            "title": "Temporary oversight exception",
            "justification": "Temporary exception while reviewer workflow is migrated.",
            "compensating_controls": ["Manual approval log", "Weekly compliance review"],
            "requested_by": "Compliance Reviewer",
            "expires_at": expires_at,
        },
    ).json()
    approved = client.patch(
        f"/risk-register/exceptions/{created['id']}",
        json={"status": "approved", "approved_by": "Compliance Lead"},
    ).json()
    events = client.get(f"/audit/assessments/{assessment['id']}/events").json()

    assert approved["status"] == "approved"
    assert approved["approved_by"] == "Compliance Lead"
    assert any(event["action"] == "policy_exception.approved" for event in events)


def test_risk_register_is_tenant_scoped():
    assessment = _create_assessment("tenant-a")
    client.post(
        f"/risk-register/assessments/{assessment['id']}/sync",
        headers={"X-Tenant-ID": "tenant-a", "X-User-Role": "admin"},
    )

    tenant_b_risks = client.get(
        "/risk-register",
        headers={"X-Tenant-ID": "tenant-b", "X-User-Role": "viewer"},
    ).json()
    tenant_b_sync = client.post(
        f"/risk-register/assessments/{assessment['id']}/sync",
        headers={"X-Tenant-ID": "tenant-b", "X-User-Role": "admin"},
    )

    assert tenant_b_risks == []
    assert tenant_b_sync.status_code == 404
