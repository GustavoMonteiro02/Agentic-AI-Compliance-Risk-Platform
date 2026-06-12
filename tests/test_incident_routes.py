from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def _create_system_and_assessment(tenant_id: str = "default") -> tuple[dict, dict]:
    headers = {"X-Tenant-ID": tenant_id, "X-User-Role": "admin", "X-User": "incident-owner"}
    system = client.post(
        "/systems",
        headers=headers,
        json={
            "name": "Incident Managed Assistant",
            "description": "AI support agent handles customer issues and can produce harmful recommendations.",
        },
    ).json()
    assessment = client.post(f"/systems/{system['id']}/assess", headers=headers).json()
    return system, assessment


def test_incident_lifecycle_and_audit_event():
    system, assessment = _create_system_and_assessment()

    created = client.post(
        "/incidents",
        json={
            "system_id": system["id"],
            "assessment_id": assessment["id"],
            "title": "Incorrect escalation recommendation",
            "description": "The AI assistant recommended an incorrect escalation path for a regulated customer issue.",
            "severity": "high",
            "owner": "AI Operations Lead",
            "impact_summary": "Potential customer harm and process breach.",
            "containment_actions": ["Disable escalation suggestions", "Notify support leads"],
            "regulatory_report_required": True,
        },
    ).json()
    updated = client.patch(
        f"/incidents/{created['id']}",
        json={
            "status": "resolved",
            "root_cause": "Missing policy routing test case.",
            "corrective_actions": ["Add regression case", "Require reviewer sign-off"],
        },
    ).json()
    listed = client.get("/incidents", params={"severity": "high"}).json()
    events = client.get(f"/audit/assessments/{assessment['id']}/events").json()

    assert created["status"] == "reported"
    assert created["containment_actions_json"] == ["Disable escalation suggestions", "Notify support leads"]
    assert updated["status"] == "resolved"
    assert updated["resolved_at"] is not None
    assert updated["corrective_actions_json"] == ["Add regression case", "Require reviewer sign-off"]
    assert any(item["id"] == created["id"] for item in listed)
    assert any(event["action"] == "incident.reported" for event in events)
    assert any(event["action"] == "incident.resolved" for event in events)


def test_regulatory_report_queue_and_submission_tracking():
    system, assessment = _create_system_and_assessment("reg-report-tenant")
    headers = {"X-Tenant-ID": "reg-report-tenant", "X-User-Role": "admin", "X-User": "incident-owner"}
    auditor_headers = {"X-Tenant-ID": "reg-report-tenant", "X-User-Role": "auditor"}

    created = client.post(
        "/incidents",
        headers=headers,
        json={
            "system_id": system["id"],
            "assessment_id": assessment["id"],
            "title": "Reportable AI incident",
            "description": "A reportable incident affected regulated customer decision support.",
            "severity": "critical",
            "regulatory_report_required": True,
        },
    ).json()
    queue_before = client.get("/incidents/regulatory-report-queue", headers=auditor_headers).json()
    submitted = client.patch(
        f"/incidents/{created['id']}",
        headers=headers,
        json={
            "regulatory_reported_at": created["detected_at"],
            "regulatory_report_reference": "REG-2026-0001",
        },
    ).json()
    queue_after = client.get("/incidents/regulatory-report-queue", headers=auditor_headers).json()
    events = client.get(f"/audit/assessments/{assessment['id']}/events", headers=auditor_headers).json()

    assert created["regulatory_report_due_at"]
    assert any(item["id"] == created["id"] for item in queue_before)
    assert submitted["regulatory_report_reference"] == "REG-2026-0001"
    assert submitted["regulatory_reported_at"]
    assert all(item["id"] != created["id"] for item in queue_after)
    assert any(event["details_json"]["regulatory_reported"] is True for event in events)


def test_incidents_are_tenant_scoped():
    system, _assessment = _create_system_and_assessment("incident-tenant-a")
    created = client.post(
        "/incidents",
        headers={"X-Tenant-ID": "incident-tenant-a", "X-User-Role": "admin"},
        json={
            "system_id": system["id"],
            "title": "Tenant scoped incident",
            "description": "Incident should only be visible inside the owning tenant.",
            "severity": "medium",
        },
    )
    tenant_b_list = client.get(
        "/incidents",
        headers={"X-Tenant-ID": "incident-tenant-b", "X-User-Role": "viewer"},
    )
    tenant_b_update = client.patch(
        f"/incidents/{created.json()['id']}",
        headers={"X-Tenant-ID": "incident-tenant-b", "X-User-Role": "admin"},
        json={"status": "triaging"},
    )

    assert created.status_code == 200
    assert tenant_b_list.json() == []
    assert tenant_b_update.status_code == 404
