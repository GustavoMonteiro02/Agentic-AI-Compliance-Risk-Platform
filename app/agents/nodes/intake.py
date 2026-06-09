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
    context = state.get("system_context", {})
    answers = {item.get("field"): item.get("answer") for item in state.get("user_answers", [])}

    domain = "unknown"
    for candidate, terms in DOMAIN_KEYWORDS.items():
        if _contains_any(normalized, terms):
            domain = candidate
            break

    affected_users = list(context.get("users_affected") or [])
    if "candidate" in normalized:
        affected_users.append("job candidates")
    if "customer" in normalized:
        affected_users.append("customers")
    if "employee" in normalized or "internal" in normalized:
        affected_users.append("employees")

    data_types = list(context.get("data_types") or [])
    if not data_types:
        if "cv" in normalized or "resume" in normalized:
            data_types.append("CVs/resumes")
        if "embedding" in normalized:
            data_types.append("embeddings")
        if "score" in normalized:
            data_types.append("scores")
        if "ticket" in normalized:
            data_types.append("support tickets")

    oversight_text = " ".join(
        str(value)
        for value in [
            context.get("human_oversight_process"),
            answers.get("human_oversight"),
            answers.get("final_decision"),
        ]
        if value
    ).lower()
    autonomy_level = (
        context.get("autonomy_level")
        or ("human-in-the-loop" if re.search(r"human|reviewed by humans|recruiter", normalized + " " + oversight_text) else "unknown")
    )
    decision_impact = context.get("decision_impact") or (
        "recommendation" if re.search(r"recommend|rank|score|prioriti", normalized) else "unknown"
    )
    deployment_status = answers.get("deployment_status") or context.get("deployment_status") or "unknown"
    model_provider = answers.get("model_provider") or context.get("model_provider")
    model_type = answers.get("model_type") or context.get("model_type")
    data_source_answer = answers.get("data_sources")
    if data_source_answer and not data_types:
        data_types.extend(part.strip() for part in data_source_answer.split(",") if part.strip())

    profile = {
        "system_name": context.get("name") or infer_system_name(description),
        "use_case": description,
        "business_unit": context.get("business_unit"),
        "system_owner": context.get("owner"),
        "technical_owner": context.get("technical_owner"),
        "business_domain": domain,
        "affected_users": affected_users,
        "external_users_affected": bool(context.get("external_users_affected", False)),
        "data_types": data_types,
        "model_provider": model_provider,
        "model_type": model_type,
        "integrations_tools_used": list(context.get("integrations_tools_used") or []),
        "personal_data": _contains_any(normalized, PERSONAL_DATA_TERMS),
        "sensitive_data": _contains_any(normalized, SENSITIVE_DATA_TERMS),
        "decision_impact": decision_impact,
        "autonomy_level": autonomy_level,
        "human_oversight": "described" if autonomy_level == "human-in-the-loop" else "unknown",
        "deployment_status": deployment_status,
        "monitoring_status": answers.get("monitoring_status") or context.get("monitoring_status"),
        "evaluation_status": answers.get("evaluation_status") or context.get("evaluation_status"),
        "security_testing_status": answers.get("security_testing_status") or context.get("security_testing_status"),
        "missing_information": [],
    }
    state["system_profile"] = profile
    state.setdefault("tool_calls", []).append({"tool_name": "intake_node", "status": "success"})
    return state
