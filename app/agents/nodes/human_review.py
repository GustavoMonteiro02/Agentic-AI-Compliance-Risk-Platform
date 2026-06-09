from app.agents.state import GovernanceAssessmentState


def human_review_node(state: GovernanceAssessmentState) -> GovernanceAssessmentState:
    state["requires_human_review"] = True
    state["human_review_status"] = "needs_review"
    state["status"] = "needs_review"
    state.setdefault("tool_calls", []).append({"tool_name": "human_review_gate", "status": "needs_review"})
    return state

