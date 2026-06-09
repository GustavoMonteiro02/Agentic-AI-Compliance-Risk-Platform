from app.agents.state import GovernanceAssessmentState


CONTROL_LIBRARY = {
    "HUMAN_OVERSIGHT": {
        "control": "Documented human review procedure for high-impact AI recommendations.",
        "evidence": ["Human oversight SOP", "Approval logs", "Escalation procedure"],
    },
    "EVALUATION": {
        "control": "Evaluation dataset and recurring quality, bias, and failure-mode testing.",
        "evidence": ["Evaluation dataset", "Evaluation report", "Bias/fairness test results"],
    },
    "AUDIT_LOGGING": {
        "control": "Log model inputs, outputs, recommendations, human decisions, and overrides.",
        "evidence": ["Audit log schema", "Retention settings", "Sample decision logs"],
    },
    "DATA_PROTECTION": {
        "control": "Document personal-data purpose, retention, access control, and DPIA triggers.",
        "evidence": ["Data flow diagram", "Retention policy", "DPIA screening"],
    },
    "SECURITY_TESTING": {
        "control": "Perform prompt-injection, data leakage, access-control, and abuse testing.",
        "evidence": ["Security test plan", "Prompt injection report", "Remediation tickets"],
    },
    "TRANSPARENCY": {
        "control": "Provide appropriate user-facing transparency and internal reviewer guidance.",
        "evidence": ["Transparency notice", "Reviewer playbook", "User communication template"],
    },
}


def control_mapper_node(state: GovernanceAssessmentState) -> GovernanceAssessmentState:
    controls = []
    profile = state["system_profile"]
    for req in state.get("retrieved_requirements", []):
        req_id = req["requirement_id"]
        key = next((name for name in CONTROL_LIBRARY if name in req_id), "HUMAN_OVERSIGHT")
        library_item = CONTROL_LIBRARY[key]
        status = "partial" if key == "HUMAN_OVERSIGHT" and profile.get("human_oversight") == "described" else "missing"
        controls.append(
            {
                "requirement_id": req_id,
                "requirement": req["title"],
                "mapped_control": library_item["control"],
                "evidence_needed": library_item["evidence"],
                "control_status": status,
            }
        )
    state["mapped_controls"] = controls
    state.setdefault("tool_calls", []).append({"tool_name": "map_requirement_to_control", "status": "success"})
    return state

