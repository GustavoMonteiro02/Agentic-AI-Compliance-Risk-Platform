from app.mcp_server.server import PROMPTS, RESOURCES, TOOLS, _prompt_reader, _resource_reader, read_resource
from app.mcp_server.runtime import runtime_config


def test_mcp_surface_exposes_required_tools_resources_and_prompts():
    for tool_name in [
        "classify_ai_system_risk",
        "search_regulatory_requirements",
        "map_requirement_to_control",
        "generate_evidence_checklist",
        "generate_ai_system_card",
        "generate_audit_report",
        "create_compliance_task",
        "calculate_compliance_score",
    ]:
        assert tool_name in TOOLS

    assert "compliance://policies/internal-ai-policy" in RESOURCES
    assert "compliance://controls/security-testing" in RESOURCES
    assert "risk_classification_prompt" in PROMPTS
    assert "human_review_prompt" in PROMPTS


def test_mcp_resource_reader_loads_policy_text():
    text = read_resource("compliance://policies/internal-ai-policy")

    assert "Human oversight" in text


def test_mcp_registered_callbacks_have_stable_names():
    resource_callback = _resource_reader("compliance://policies/internal-ai-policy")
    prompt_callback = _prompt_reader("human_review_prompt", "Require human review.")

    assert resource_callback.__name__ == "read_compliance_policies_internal_ai_policy"
    assert prompt_callback.__name__ == "read_human_review_prompt"
    assert "Human oversight" in resource_callback()
    assert prompt_callback() == "Require human review."


def test_mcp_runtime_config_exposes_deployment_surface():
    config = runtime_config()

    assert config["server_name"] == "ai-governance-compliance"
    assert config["transport"] == "stdio"
    assert config["tool_count"] == len(TOOLS)
    assert config["resource_count"] == len(RESOURCES)
    assert config["prompt_count"] == len(PROMPTS)
