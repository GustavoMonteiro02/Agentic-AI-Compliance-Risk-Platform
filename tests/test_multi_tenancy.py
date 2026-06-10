from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def _headers(tenant_id: str, role: str = "admin") -> dict[str, str]:
    return {"X-Tenant-ID": tenant_id, "X-User-Role": role, "X-User": f"{tenant_id}-user"}


def _create_system(tenant_id: str, name: str) -> dict:
    return client.post(
        "/systems",
        headers=_headers(tenant_id),
        json={"name": name, "description": "AI assistant in HR analyzes CVs and recommends candidates."},
    ).json()


def test_system_inventory_is_scoped_by_tenant():
    tenant_a_system = _create_system("tenant-a", "Tenant A System")
    _create_system("tenant-b", "Tenant B System")

    tenant_a_inventory = client.get("/systems", headers=_headers("tenant-a", "viewer")).json()
    tenant_b_get = client.get(f"/systems/{tenant_a_system['id']}", headers=_headers("tenant-b", "viewer"))

    assert [item["name"] for item in tenant_a_inventory] == ["Tenant A System"]
    assert tenant_b_get.status_code == 404


def test_assessment_reports_and_evidence_are_scoped_by_tenant():
    system = _create_system("tenant-a", "Tenant A Assessment System")
    assessment = client.post(f"/systems/{system['id']}/assess", headers=_headers("tenant-a")).json()

    tenant_b_assessment = client.get(f"/assessments/{assessment['id']}", headers=_headers("tenant-b", "viewer"))
    tenant_b_report = client.get(f"/reports/{assessment['id']}", headers=_headers("tenant-b", "viewer"))
    tenant_b_evidence = client.get(f"/evidence/assessments/{assessment['id']}", headers=_headers("tenant-b", "viewer"))

    assert tenant_b_assessment.status_code == 404
    assert tenant_b_report.status_code == 404
    assert tenant_b_evidence.status_code == 404


def test_audit_events_are_scoped_by_tenant():
    system = _create_system("tenant-a", "Tenant A Audit System")
    assessment = client.post(f"/systems/{system['id']}/assess", headers=_headers("tenant-a")).json()
    item = client.get(f"/evidence/assessments/{assessment['id']}", headers=_headers("tenant-a", "viewer")).json()[0]
    client.patch(f"/evidence/items/{item['id']}", headers=_headers("tenant-a"), json={"status": "uploaded"})

    tenant_a_events = client.get(f"/audit/assessments/{assessment['id']}/events", headers=_headers("tenant-a", "auditor")).json()
    tenant_b_events = client.get(f"/audit/assessments/{assessment['id']}/events", headers=_headers("tenant-b", "auditor")).json()

    assert tenant_a_events[0]["tenant_id"] == "tenant-a"
    assert tenant_a_events[0]["action"] == "evidence.updated"
    assert tenant_b_events == []
