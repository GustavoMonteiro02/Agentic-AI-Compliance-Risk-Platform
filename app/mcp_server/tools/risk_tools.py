from app.agents.nodes.risk_classifier import risk_classifier_node
from app.agents.state import GovernanceAssessmentState


def classify_ai_system_risk(system_profile: dict) -> dict:
    state: GovernanceAssessmentState = {"system_profile": system_profile, "tool_calls": []}
    return risk_classifier_node(state)["risk_classification"]


def calculate_compliance_score(mapped_controls: list[dict], evidence_items: list[dict]) -> dict:
    control_score = _ratio(item.get("control_status") == "implemented" for item in mapped_controls)
    evidence_score = _ratio(item.get("status") in {"generated", "uploaded", "approved"} for item in evidence_items)
    score = round((control_score * 0.6 + evidence_score * 0.4) * 100, 1)
    return {"score": score, "control_score": control_score, "evidence_score": evidence_score}


def _ratio(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0

