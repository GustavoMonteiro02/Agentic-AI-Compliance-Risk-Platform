import re

from app.agents.state import GovernanceAssessmentState


DOMAIN_KEYWORDS = {
    "employment": ["hr", "recruit", "candidate", "cv", "resume", "hiring", "employee"],
    "financial_services": ["credit", "loan", "insurance", "fraud", "payment", "invoice"],
    "healthcare": ["health", "patient", "medical", "appointment", "triage"],
    "legal": ["legal", "contract", "litigation", "document review"],
    "customer_support": ["customer", "support", "refund", "ticket"],
}

PERSONAL_DATA_TERMS = ["personal data", "cv", "resume", "email", "name", "customer", "candidate"]
SENSITIVE_DATA_TERMS = ["health", "biometric", "ethnicity", "political", "religion", "union"]


def _contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def infer_system_name(description: str) -> str:
    text = description.lower()
    if _contains_any(text, ["cv", "resume", "candidate", "recruit"]):
        return "Recruitment CV Screening Assistant"
    if _contains_any(text, ["customer", "support", "ticket"]):
        return "Customer Support AI Copilot"
    if _contains_any(text, ["invoice", "payment"]):
        return "Invoice Validation AI Agent"
    if _contains_any(text, ["knowledge base", "internal documents"]):
        return "Internal Knowledge Base Assistant"
    return "AI System"


def intake_node(state: GovernanceAssessmentState) -> GovernanceAssessmentState:
    description = state["raw_user_description"]
    normalized = description.lower()

    domain = "unknown"
    for candidate, terms in DOMAIN_KEYWORDS.items():
        if _contains_any(normalized, terms):
            domain = candidate
            break

    affected_users = []
    if "candidate" in normalized:
        affected_users.append("job candidates")
    if "customer" in normalized:
        affected_users.append("customers")
    if "employee" in normalized or "internal" in normalized:
        affected_users.append("employees")

    data_types = []
    if "cv" in normalized or "resume" in normalized:
        data_types.append("CVs/resumes")
    if "embedding" in normalized:
        data_types.append("embeddings")
    if "score" in normalized:
        data_types.append("scores")
    if "ticket" in normalized:
        data_types.append("support tickets")

    autonomy_level = "human-in-the-loop" if re.search(r"human|reviewed by humans|recruiter", normalized) else "unknown"
    decision_impact = "recommendation" if re.search(r"recommend|rank|score|prioriti", normalized) else "unknown"

    profile = {
        "system_name": infer_system_name(description),
        "use_case": description,
        "business_domain": domain,
        "affected_users": affected_users,
        "data_types": data_types,
        "personal_data": _contains_any(normalized, PERSONAL_DATA_TERMS),
        "sensitive_data": _contains_any(normalized, SENSITIVE_DATA_TERMS),
        "decision_impact": decision_impact,
        "autonomy_level": autonomy_level,
        "human_oversight": "described" if autonomy_level == "human-in-the-loop" else "unknown",
        "deployment_status": "unknown",
        "missing_information": [],
    }
    state["system_profile"] = profile
    state.setdefault("tool_calls", []).append({"tool_name": "intake_node", "status": "success"})
    return state

