import json
from typing import Any

from pydantic import ValidationError

from app.agents.state import GovernanceAssessmentState
from app.llm.provider import OptionalLLMProvider
from app.prompts.registry import get_prompt
from app.schemas.assessment import EvidenceItem, GapAnalysis, GeneratedDocument, MappedControl, RiskClassification


def _run_structured_refinement(provider: Any, system_prompt: str, user_prompt: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if hasattr(provider, "structured_json_result"):
        result = provider.structured_json_result(system_prompt, user_prompt)
        if not result:
            return None, {}
        refined, metadata = result
        return refined, metadata
    return provider.structured_json(system_prompt, user_prompt), {}


def llm_refiner_node(state: GovernanceAssessmentState) -> GovernanceAssessmentState:
    provider = OptionalLLMProvider()
    prompt = get_prompt("llm_refiner")
    provider_mode = getattr(provider, "provider_name", "openai")
    if not provider.enabled():
        state.setdefault("tool_calls", []).append(
            {
                "tool_name": "llm_refiner",
                "status": "skipped",
                "mode": "deterministic",
                "prompt_name": prompt.name,
                "prompt_version": prompt.version,
            }
        )
        return state

    payload = {
        "system_profile": state.get("system_profile", {}),
        "risk_classification": state.get("risk_classification", {}),
        "retrieved_requirements": state.get("retrieved_requirements", []),
        "mapped_controls": state.get("mapped_controls", []),
        "gap_analysis": state.get("gap_analysis", {}),
        "evidence_checklist": state.get("evidence_checklist", []),
    }
    user_prompt = prompt.user_template.format(assessment_json=json.dumps(payload, ensure_ascii=True))
    try:
        refined, metadata = _run_structured_refinement(provider, prompt.system, user_prompt)
        if not refined:
            state.setdefault("tool_calls", []).append(
                {
                    "tool_name": "llm_refiner",
                    "status": "skipped",
                    "mode": provider_mode,
                    "reason": "empty_response",
                    "prompt_name": prompt.name,
                    "prompt_version": prompt.version,
                    **metadata,
                }
            )
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
        state.setdefault("tool_calls", []).append(
            {
                "tool_name": "llm_refiner",
                "status": "success",
                "mode": provider_mode,
                "prompt_name": prompt.name,
                "prompt_version": prompt.version,
                "schema_validated": True,
                "applied_sections": sorted(
                    key
                    for key in [
                        "risk_classification",
                        "mapped_controls",
                        "gap_analysis",
                        "evidence_checklist",
                        "ai_system_card_markdown",
                        "audit_report_markdown",
                    ]
                    if refined.get(key)
                ),
                **metadata,
            }
        )
    except (KeyError, ValidationError, ValueError, Exception) as exc:
        state.setdefault("errors", []).append({"node": "llm_refiner", "error": str(exc)})
        state.setdefault("tool_calls", []).append(
            {
                "tool_name": "llm_refiner",
                "status": "failed",
                "mode": provider_mode,
                "prompt_name": prompt.name,
                "prompt_version": prompt.version,
                "schema_validated": False,
                "fallback": "deterministic_state_preserved",
            }
        )
    return state
