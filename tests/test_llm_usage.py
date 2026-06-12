from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.main import app
from app.services.llm_usage_service import summarize_llm_usage


client = TestClient(app)


def test_llm_usage_summary_aggregates_tokens_latency_and_cost():
    summary = summarize_llm_usage(
        [
            SimpleNamespace(
                tool_calls=[
                    {
                        "tool_name": "llm_refiner",
                        "status": "success",
                        "provider": "openai",
                        "model": "gpt-test",
                        "prompt_version": "2026.v1",
                        "prompt_tokens": 100,
                        "completion_tokens": 50,
                        "total_tokens": 150,
                        "latency_ms": 25.5,
                    },
                    {"tool_name": "generate_audit_report", "status": "success"},
                ]
            )
        ],
        prompt_cost_per_1k_tokens=0.1,
        completion_cost_per_1k_tokens=0.2,
        assessment_id="assessment-1",
    )

    assert summary.assessment_id == "assessment-1"
    assert summary.assessment_count == 1
    assert summary.total_tool_calls == 2
    assert summary.llm_call_count == 1
    assert summary.prompt_tokens == 100
    assert summary.completion_tokens == 50
    assert summary.total_tokens == 150
    assert summary.total_latency_ms == 25.5
    assert summary.average_latency_ms == 25.5
    assert summary.estimated_cost_usd == 0.02
    assert summary.providers == ["openai"]
    assert summary.models == ["gpt-test"]
    assert summary.prompt_versions == ["2026.v1"]


def test_assessment_llm_usage_endpoint_is_tenant_scoped():
    headers = {"X-Tenant-ID": "llm-usage", "X-User-Role": "admin", "X-User": "usage-admin"}
    system = client.post(
        "/systems",
        headers=headers,
        json={
            "name": "LLM Usage System",
            "description": "AI assistant in HR analyzes CVs and recommends candidates to recruiters.",
        },
    ).json()
    assessment = client.post(f"/systems/{system['id']}/assess", headers=headers).json()

    assessment_usage = client.get(f"/assessments/{assessment['id']}/llm-usage", headers=headers)
    tenant_usage = client.get("/assessments/llm-usage", headers=headers)
    other_tenant_usage = client.get(
        "/assessments/llm-usage",
        headers={"X-Tenant-ID": "llm-usage-other", "X-User-Role": "auditor"},
    )

    assert assessment_usage.status_code == 200
    assert assessment_usage.json()["assessment_id"] == assessment["id"]
    assert assessment_usage.json()["llm_call_count"] >= 1
    assert tenant_usage.json()["assessment_count"] >= 1
    assert tenant_usage.json()["llm_call_count"] >= assessment_usage.json()["llm_call_count"]
    assert other_tenant_usage.json()["assessment_count"] == 0
