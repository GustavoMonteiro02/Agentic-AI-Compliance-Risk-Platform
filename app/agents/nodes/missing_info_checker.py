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
    missing.extend(["evaluation_status", "audit_logging", "fallback_process"])

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

