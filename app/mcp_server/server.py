from pathlib import Path

from app.mcp_server.prompts.gap_prompt import GAP_ANALYSIS_PROMPT
from app.mcp_server.prompts.report_prompt import AUDIT_REPORT_PROMPT
from app.mcp_server.prompts.risk_prompt import RISK_CLASSIFICATION_PROMPT
from app.mcp_server.resources.controls import CONTROL_RESOURCES
from app.mcp_server.resources.policies import POLICY_RESOURCES
from app.mcp_server.resources.regulations import REGULATION_RESOURCES
from app.mcp_server.tools.control_tools import create_compliance_task, map_requirement_to_control
from app.mcp_server.tools.evidence_tools import generate_evidence_checklist
from app.mcp_server.tools.report_tools import generate_ai_system_card, generate_audit_report
from app.mcp_server.tools.requirement_tools import search_regulatory_requirements
from app.mcp_server.tools.risk_tools import calculate_compliance_score, classify_ai_system_risk


TOOLS = {
    "classify_ai_system_risk": classify_ai_system_risk,
    "search_regulatory_requirements": search_regulatory_requirements,
    "map_requirement_to_control": map_requirement_to_control,
    "generate_evidence_checklist": generate_evidence_checklist,
    "generate_ai_system_card": generate_ai_system_card,
    "generate_audit_report": generate_audit_report,
    "create_compliance_task": create_compliance_task,
    "calculate_compliance_score": calculate_compliance_score,
}

RESOURCES = {**POLICY_RESOURCES, **REGULATION_RESOURCES, **CONTROL_RESOURCES}

PROMPTS = {
    "risk_classification_prompt": RISK_CLASSIFICATION_PROMPT,
    "regulatory_retrieval_prompt": "Retrieve policy and regulatory summaries relevant to the AI system profile.",
    "gap_analysis_prompt": GAP_ANALYSIS_PROMPT,
    "control_mapping_prompt": "Map each requirement to practical controls and evidence.",
    "system_card_prompt": "Generate a draft AI system card with required governance sections.",
    "audit_report_prompt": AUDIT_REPORT_PROMPT,
    "human_review_prompt": "Require human approval, rejection, or a request for more evidence.",
}


def read_resource(uri: str) -> str:
    path = RESOURCES[uri]
    return Path(path).read_text(encoding="utf-8")


def create_fastmcp_server():
    """Create a FastMCP server when fastmcp is installed.

    The dictionary exports above keep the MCP surface testable even when the runtime server is not used.
    """
    from fastmcp import FastMCP

    mcp = FastMCP("ai-governance-compliance")
    for name, tool in TOOLS.items():
        mcp.tool(name=name)(tool)

    for uri in RESOURCES:
        mcp.resource(uri)(lambda uri=uri: read_resource(uri))

    for name, prompt in PROMPTS.items():
        mcp.prompt(name=name)(lambda prompt=prompt: prompt)
    return mcp


if __name__ == "__main__":
    create_fastmcp_server().run()

