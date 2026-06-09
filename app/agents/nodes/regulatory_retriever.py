from app.agents.state import GovernanceAssessmentState
from app.rag.retriever import LocalComplianceRetriever


def regulatory_retriever_node(state: GovernanceAssessmentState) -> GovernanceAssessmentState:
    profile = state["system_profile"]
    risk = state["risk_classification"]
    query = " ".join(
        [
            profile.get("business_domain", ""),
            profile.get("use_case", ""),
            " ".join(risk.get("risk_factors", [])),
            "human oversight evaluation audit logging data protection security transparency",
        ]
    )
    requirements = LocalComplianceRetriever().search(query, top_k=7)
    state["retrieved_requirements"] = requirements
    state.setdefault("tool_calls", []).append(
        {"tool_name": "search_regulatory_requirements", "status": "success", "result_count": len(requirements)}
    )
    return state

