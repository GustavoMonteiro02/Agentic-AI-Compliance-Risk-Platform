from app.mcp_server.server import PROMPTS, RESOURCES, TOOLS, read_resource


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
