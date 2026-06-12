from app.agents.state import GovernanceAssessmentState
from app.llm.provider import OptionalLLMProvider


HIGH_RISK_DOMAINS = {"employment", "financial_services", "healthcare"}


def risk_classifier_node(state: GovernanceAssessmentState) -> GovernanceAssessmentState:
    profile = state["system_profile"]
    factors: list[str] = []
    domain = profile.get("business_domain")

    if domain in HIGH_RISK_DOMAINS:
        factors.append(f"{domain.replace('_', ' ')} context")
    if profile.get("personal_data"):
        factors.append("personal data processing")
    if profile.get("sensitive_data"):
        factors.append("sensitive data processing")
    if profile.get("decision_impact") != "unknown":
        factors.append("decision support or ranking")
    if profile.get("autonomy_level") == "unknown":
        factors.append("unclear autonomy level")
    if profile.get("human_oversight") == "unknown":
        factors.append("unclear human oversight")

    if domain in HIGH_RISK_DOMAINS and profile.get("decision_impact") != "unknown":
        risk_level = "high"
        confidence = 0.86
    elif profile.get("personal_data") and profile.get("decision_impact") != "unknown":
        risk_level = "medium"
        confidence = 0.72
    elif profile.get("personal_data"):
        risk_level = "limited"
        confidence = 0.65
    else:
        risk_level = "minimal"
        confidence = 0.58

    requires_additional = bool(profile.get("missing_information")) and confidence < 0.8
    reasoning_summary = (
        "Preliminary classification based on domain, data sensitivity, decision impact, "
        "autonomy, and oversight signals. Human compliance review is required."
    )
    provider = OptionalLLMProvider()
    provider_mode = getattr(provider, "provider_name", "openai")
    llm_advice = None
    llm_error = None
    try:
        llm_advice = provider.advisory_completion(
            "You are an AI governance assistant. Do not provide legal advice or final compliance claims.",
            f"Summarize the risk rationale for this AI system profile in one sentence: {profile}",
        )
    except Exception as exc:
        llm_error = str(exc)
        state.setdefault("errors", []).append({"node": "risk_classifier", "error": llm_error})
    if llm_advice:
        reasoning_summary = f"{reasoning_summary} LLM advisory note: {llm_advice}"

    state["risk_classification"] = {
        "risk_level": risk_level,
        "confidence": confidence,
        "risk_factors": factors,
        "reasoning_summary": reasoning_summary,
        "requires_human_review": True,
        "requires_additional_information": requires_additional,
    }
    state["requires_human_review"] = True
    state.setdefault("tool_calls", []).append(
        {
            "tool_name": "classify_ai_system_risk",
            "status": "success" if not llm_error else "failed",
            "mode": provider_mode if llm_advice or llm_error else "deterministic",
            "fallback": "deterministic_risk_preserved" if llm_error else None,
        }
    )
    return state
