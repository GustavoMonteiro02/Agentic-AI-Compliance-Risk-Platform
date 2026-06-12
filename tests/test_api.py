from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["kind"] == "liveness"


def test_request_id_is_returned_and_echoed():
    response = client.get("/health", headers={"X-Request-ID": "req-test-123"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-test-123"


def test_http_errors_use_problem_shape_with_legacy_detail():
    response = client.get("/systems/not-found")

    assert response.status_code == 404
    payload = response.json()
    assert payload["status"] == 404
    assert payload["detail"] == "AI system not found"
    assert payload["error"]["code"] == "not_found"
    assert payload["error"]["request_id"] == response.headers["x-request-id"]


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


def test_list_endpoints_support_pagination_headers():
    headers = {"X-User-Role": "admin"}
    for index in range(3):
        response = client.post(
            "/systems",
            headers=headers,
            json={
                "name": f"Paginated System {index}",
                "description": "AI assistant in HR analyzes CVs and recommends candidates to recruiters.",
            },
        )
        assert response.status_code == 200

    response = client.get("/systems?limit=2&offset=1")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert int(response.headers["x-total-count"]) >= 3
    assert response.headers["x-limit"] == "2"
    assert response.headers["x-offset"] == "1"


def test_pagination_rejects_unbounded_limits():
    response = client.get("/systems?limit=251")

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
    assert payload["detail"]


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


def test_audit_package_exports_json_and_zip():
    admin_headers = {"X-User-Role": "admin", "X-User": "system-owner"}
    auditor_headers = {"X-User-Role": "auditor", "X-User": "audit-lead"}
    system_response = client.post(
        "/systems",
        headers=admin_headers,
        json={
            "name": "Audit Package System",
            "description": "AI assistant in HR analyzes CVs and recommends candidates to recruiters.",
        },
    )
    assessment = client.post(f"/systems/{system_response.json()['id']}/assess", headers=admin_headers).json()

    package_response = client.get(f"/audit/assessments/{assessment['id']}/package", headers=auditor_headers)
    zip_response = client.get(f"/audit/assessments/{assessment['id']}/package.zip", headers=auditor_headers)

    assert package_response.status_code == 200
    package = package_response.json()
    assert package["manifest"]["package_type"] == "ai_governance_audit_package"
    assert package["manifest"]["assessment_id"] == assessment["id"]
    assert package["system"]["id"] == assessment["system_id"]
    assert package["assessment"]["id"] == assessment["id"]
    assert package["mapped_controls"]
    assert package["evidence_items"]
    assert package["audit_report"]["content_markdown"].startswith("# Audit Readiness Report")
    assert package["system_card"]["content_markdown"].startswith("# AI System Card")
    assert package["summary"]["control_count"] == len(package["mapped_controls"])

    assert zip_response.status_code == 200
    assert zip_response.headers["content-type"] == "application/zip"
    with ZipFile(BytesIO(zip_response.content)) as archive:
        assert set(archive.namelist()) == {
            "manifest.json",
            "audit_package.json",
            "reports/audit_report.md",
            "reports/system_card.md",
        }
        assert b"ai_governance_audit_package" in archive.read("manifest.json")


def test_audit_package_is_tenant_scoped():
    tenant_a_admin_headers = {"X-Tenant-ID": "audit-tenant-a", "X-User-Role": "admin"}
    tenant_b_auditor_headers = {"X-Tenant-ID": "audit-tenant-b", "X-User-Role": "auditor"}
    system_response = client.post(
        "/systems",
        headers=tenant_a_admin_headers,
        json={
            "name": "Tenant Scoped Audit Package System",
            "description": "AI assistant in HR analyzes CVs and recommends candidates to recruiters.",
        },
    )
    assessment = client.post(
        f"/systems/{system_response.json()['id']}/assess",
        headers=tenant_a_admin_headers,
    ).json()

    response = client.get(f"/audit/assessments/{assessment['id']}/package", headers=tenant_b_auditor_headers)

    assert response.status_code == 404


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
