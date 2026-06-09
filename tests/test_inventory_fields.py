from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_inventory_accepts_full_governance_fields():
    response = client.post(
        "/systems",
        json={
            "name": "Healthcare Appointment Prioritization Assistant",
            "description": "AI system prioritizes healthcare appointments for clinicians to review.",
            "business_unit": "Clinical Operations",
            "owner": "Clinical Safety Lead",
            "technical_owner": "AI Platform Lead",
            "deployment_status": "internal",
            "users_affected": ["patients", "clinicians"],
            "external_users_affected": True,
            "data_types": ["appointment notes", "patient messages"],
            "model_provider": "OpenAI",
            "model_type": "LLM workflow",
            "decision_impact": "recommendation",
            "autonomy_level": "human-in-the-loop",
            "human_oversight_process": "Clinicians review every prioritization before action.",
            "integrations_tools_used": ["EHR", "ticketing system"],
            "monitoring_status": "Dashboard planned",
            "evaluation_status": "Clinical validation pending",
            "security_testing_status": "Security review scheduled",
        },
    )

    assert response.status_code == 200
    system = response.json()
    assert system["external_users_affected"] is True
    assert system["integrations_tools_used"] == ["EHR", "ticketing system"]
    assert system["monitoring_status"] == "Dashboard planned"

    assessment = client.post(f"/systems/{system['id']}/assess").json()
    profile = assessment["profile"]
    assert profile["external_users_affected"] is True
    assert profile["integrations_tools_used"] == ["EHR", "ticketing system"]
    assert profile["monitoring_status"] == "Dashboard planned"
    assert "Clinical validation pending" in assessment["ai_system_card"]["content_markdown"]

