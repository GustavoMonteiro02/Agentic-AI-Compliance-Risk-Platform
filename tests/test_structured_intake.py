from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_assessment_uses_inventory_fields_and_follow_up_answers():
    system = client.post(
        "/systems",
        json={
            "name": "Credit Risk Scoring Assistant",
            "description": "AI system scores loan applications and recommends review priority.",
            "business_unit": "Retail Banking",
            "owner": "Credit Risk Lead",
            "deployment_status": "prototype",
            "users_affected": ["loan applicants"],
            "data_types": ["application data", "credit history"],
            "model_provider": "OpenAI",
            "model_type": "LLM workflow",
        },
    ).json()

    assessment = client.post(
        f"/systems/{system['id']}/assess",
        json={
            "user_answers": [
                {"field": "evaluation_status", "answer": "Evaluation dataset is drafted."},
                {"field": "audit_logging", "answer": "Outputs and reviewer decisions are logged."},
                {"field": "fallback_process", "answer": "Manual review queue exists."},
            ]
        },
    ).json()

    profile = assessment["profile"]
    assert profile["system_name"] == "Credit Risk Scoring Assistant"
    assert profile["business_unit"] == "Retail Banking"
    assert profile["system_owner"] == "Credit Risk Lead"
    assert profile["deployment_status"] == "prototype"
    assert profile["data_types"] == ["application data", "credit history"]
    assert profile["model_provider"] == "OpenAI"
    assert "evaluation_status" not in profile["missing_information"]
    assert "OpenAI / LLM workflow" in assessment["ai_system_card"]["content_markdown"]

