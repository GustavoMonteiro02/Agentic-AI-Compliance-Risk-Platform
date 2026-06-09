from app.agents.state import GovernanceAssessmentState


QUESTION_BANK = {
    "deployment_status": "Is the system in prototype, internal production, or external production?",
    "data_sources": "What are the main data sources and retention period?",
    "evaluation_status": "Is there an evaluation dataset and documented evaluation report?",
    "audit_logging": "Are model outputs, recommendations, and human decisions logged?",
    "fallback_process": "Is there a documented fallback or escalation process?",
}


def missing_info_checker_node(state: GovernanceAssessmentState) -> GovernanceAssessmentState:
    profile = state["system_profile"]
    missing: list[str] = []
    if profile.get("deployment_status") == "unknown":
        missing.append("deployment_status")
    if not profile.get("data_types"):
        missing.append("data_sources")
    if profile.get("human_oversight") == "unknown":
        missing.append("human_oversight")
    answered_fields = {item.get("field") for item in state.get("user_answers", [])}
    if not profile.get("evaluation_status") and "evaluation_status" not in answered_fields:
        missing.append("evaluation_status")
    if not profile.get("monitoring_status") and "monitoring_status" not in answered_fields:
        missing.append("monitoring_status")
    if not profile.get("security_testing_status") and "security_testing_status" not in answered_fields:
        missing.append("security_testing_status")
    for optional_field in ["audit_logging", "fallback_process"]:
        if optional_field not in answered_fields:
            missing.append(optional_field)

    questions = [
        {"field": key, "question": QUESTION_BANK.get(key, f"Please clarify {key}."), "priority": "high"}
        for key in dict.fromkeys(missing)
        if key in QUESTION_BANK or key == "human_oversight"
    ]
    for question in questions:
        if question["field"] == "human_oversight":
            question["question"] = "Is the final decision made by a human, automatically, or both?"

    profile["missing_information"] = list(dict.fromkeys(missing))
    state["missing_information"] = profile["missing_information"]
    state["follow_up_questions"] = questions[:5]
    state.setdefault("tool_calls", []).append({"tool_name": "missing_info_checker", "status": "success"})
    return state
