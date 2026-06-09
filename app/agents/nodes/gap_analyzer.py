from app.agents.state import GovernanceAssessmentState


def gap_analyzer_node(state: GovernanceAssessmentState) -> GovernanceAssessmentState:
    critical = []
    medium = []
    low = []
    actions = []

    for control in state.get("mapped_controls", []):
        status = control["control_status"]
        if status == "implemented":
            continue
        gap = {
            "gap": f"{control['requirement']} control is {status}",
            "risk": "High" if status == "missing" else "Medium",
            "recommended_action": f"Implement control: {control['mapped_control']}",
        }
        if status == "missing":
            critical.append(gap)
        elif status == "partial":
            medium.append(gap)
        else:
            low.append(gap)
        actions.append(gap["recommended_action"])

    if state["risk_classification"]["risk_level"] in {"high", "unacceptable"} and not critical:
        medium.append(
            {
                "gap": "High-risk system needs documented reviewer approval before production use",
                "risk": "Medium",
                "recommended_action": "Submit the assessment to a compliance officer for review.",
            }
        )
        actions.append("Submit the assessment to a compliance officer for review.")

    state["gap_analysis"] = {
        "overall_status": "not_ready_for_audit" if critical else "needs_review",
        "critical_gaps": critical,
        "medium_gaps": medium,
        "low_gaps": low,
        "priority_actions": actions[:7],
    }
    state.setdefault("tool_calls", []).append({"tool_name": "gap_analysis", "status": "success"})
    return state

