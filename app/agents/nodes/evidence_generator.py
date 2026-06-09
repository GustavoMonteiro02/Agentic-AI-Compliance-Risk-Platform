from app.agents.state import GovernanceAssessmentState


OWNER_BY_EVIDENCE = {
    "Human oversight SOP": "Compliance",
    "Approval logs": "Compliance",
    "Escalation procedure": "Compliance",
    "Evaluation dataset": "AI Engineering",
    "Evaluation report": "AI Engineering",
    "Bias/fairness test results": "AI Engineering",
    "Data flow diagram": "Data Protection",
    "Retention policy": "Data Protection",
    "DPIA screening": "Data Protection",
    "Security test plan": "Security",
    "Prompt injection report": "Security",
}


def evidence_generator_node(state: GovernanceAssessmentState) -> GovernanceAssessmentState:
    items = {}
    for control in state.get("mapped_controls", []):
        for evidence in control["evidence_needed"]:
            items[evidence] = {
                "evidence": evidence,
                "status": "partial" if control["control_status"] == "partial" else "missing",
                "priority": "high" if control["control_status"] in {"missing", "partial"} else "medium",
                "owner": OWNER_BY_EVIDENCE.get(evidence, "AI Engineering"),
            }
    items.setdefault(
        "AI system card",
        {"evidence": "AI system card", "status": "generated", "priority": "high", "owner": "AI Engineering"},
    )
    state["evidence_checklist"] = list(items.values())
    state.setdefault("tool_calls", []).append({"tool_name": "generate_evidence_checklist", "status": "success"})
    return state

