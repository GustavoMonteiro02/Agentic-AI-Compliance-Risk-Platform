import json

from pydantic import ValidationError

from app.agents.state import GovernanceAssessmentState
from app.llm.provider import OptionalLLMProvider
from app.schemas.assessment import EvidenceItem, GapAnalysis, GeneratedDocument, MappedControl, RiskClassification


SYSTEM_PROMPT = """You are an AI governance and compliance engineering assistant.
You help prepare audit-readiness drafts, not legal advice.
Never claim final compliance. Always require qualified human review.
Return only valid JSON matching the requested keys."""


def llm_refiner_node(state: GovernanceAssessmentState) -> GovernanceAssessmentState:
    provider = OptionalLLMProvider()
    if not provider.enabled():
        state.setdefault("tool_calls", []).append({"tool_name": "llm_refiner", "status": "skipped", "mode": "deterministic"})
        return state

    payload = {
        "system_profile": state.get("system_profile", {}),
        "risk_classification": state.get("risk_classification", {}),
        "retrieved_requirements": state.get("retrieved_requirements", []),
        "mapped_controls": state.get("mapped_controls", []),
        "gap_analysis": state.get("gap_analysis", {}),
        "evidence_checklist": state.get("evidence_checklist", []),
    }
    user_prompt = f"""
Refine this governance assessment as production-quality structured output.

Return JSON with exactly these keys:
- risk_classification: object with risk_level, confidence, risk_factors, reasoning_summary, requires_human_review, requires_additional_information
- mapped_controls: array of objects with requirement_id, requirement, mapped_control, evidence_needed, control_status
- gap_analysis: object with overall_status, critical_gaps, medium_gaps, low_gaps, priority_actions
- evidence_checklist: array of objects with evidence, status, priority, owner
- ai_system_card_markdown: markdown string
- audit_report_markdown: markdown string

Keep all analysis preliminary. Do not provide legal advice. Require human review.

Assessment:
{json.dumps(payload, ensure_ascii=True)}
"""
    try:
        refined = provider.structured_json(SYSTEM_PROMPT, user_prompt)
        if not refined:
            return state

        state["risk_classification"] = RiskClassification.model_validate(refined["risk_classification"]).model_dump()
        state["mapped_controls"] = [
            MappedControl.model_validate(item).model_dump() for item in refined.get("mapped_controls", [])
        ] or state.get("mapped_controls", [])
        state["gap_analysis"] = GapAnalysis.model_validate(refined["gap_analysis"]).model_dump()
        state["evidence_checklist"] = [
            EvidenceItem.model_validate(item).model_dump() for item in refined.get("evidence_checklist", [])
        ] or state.get("evidence_checklist", [])
        if refined.get("ai_system_card_markdown"):
            state["ai_system_card"] = GeneratedDocument(
                title=state["ai_system_card"]["title"],
                content_markdown=refined["ai_system_card_markdown"],
                content_json=state["ai_system_card"].get("content_json", {}),
                status="draft",
            ).model_dump()
        if refined.get("audit_report_markdown"):
            state["audit_report"] = GeneratedDocument(
                title=state["audit_report"]["title"],
                content_markdown=refined["audit_report_markdown"],
                content_json=state["audit_report"].get("content_json", {}),
                status="draft",
            ).model_dump()
        state.setdefault("tool_calls", []).append({"tool_name": "llm_refiner", "status": "success", "mode": "openai"})
    except (KeyError, ValidationError, ValueError, Exception) as exc:
        state.setdefault("errors", []).append({"node": "llm_refiner", "error": str(exc)})
        state.setdefault("tool_calls", []).append({"tool_name": "llm_refiner", "status": "failed", "mode": "openai"})
    return state
