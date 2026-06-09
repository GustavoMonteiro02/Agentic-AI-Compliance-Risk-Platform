from app.agents.state import GovernanceAssessmentState


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
    state["risk_classification"] = {
        "risk_level": risk_level,
        "confidence": confidence,
        "risk_factors": factors,
        "reasoning_summary": (
            "Preliminary classification based on domain, data sensitivity, decision impact, "
            "autonomy, and oversight signals. Human compliance review is required."
        ),
        "requires_human_review": True,
        "requires_additional_information": requires_additional,
    }
    state["requires_human_review"] = True
    state.setdefault("tool_calls", []).append({"tool_name": "classify_ai_system_risk", "status": "success"})
    return state
