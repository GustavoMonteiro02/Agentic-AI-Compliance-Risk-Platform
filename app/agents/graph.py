from uuid import uuid4

from app.agents.nodes.audit_report_generator import audit_report_generator_node
from app.agents.nodes.control_mapper import control_mapper_node
from app.agents.nodes.evidence_generator import evidence_generator_node
from app.agents.nodes.gap_analyzer import gap_analyzer_node
from app.agents.nodes.human_review import human_review_node
from app.agents.nodes.intake import intake_node
from app.agents.nodes.missing_info_checker import missing_info_checker_node
from app.agents.nodes.regulatory_retriever import regulatory_retriever_node
from app.agents.nodes.risk_classifier import risk_classifier_node
from app.agents.nodes.system_card_generator import system_card_generator_node
from app.agents.state import GovernanceAssessmentState
from app.schemas.assessment import GovernanceAssessment


WORKFLOW_NODE_NAMES = [
    "intake",
    "missing_info_checker",
    "risk_classifier",
    "regulatory_retriever",
    "control_mapper",
    "gap_analyzer",
    "evidence_generator",
    "system_card_generator",
    "audit_report_generator",
    "human_review",
]


def run_governance_assessment(system_id: str, description: str) -> GovernanceAssessment:
    state: GovernanceAssessmentState = {
        "assessment_id": str(uuid4()),
        "system_id": system_id,
        "raw_user_description": description,
        "tool_calls": [],
        "errors": [],
        "status": "draft",
    }
    for node in [
        intake_node,
        missing_info_checker_node,
        risk_classifier_node,
        regulatory_retriever_node,
        control_mapper_node,
        gap_analyzer_node,
        evidence_generator_node,
        system_card_generator_node,
        audit_report_generator_node,
        human_review_node,
    ]:
        state = node(state)

    return GovernanceAssessment(
        id=state["assessment_id"],
        system_id=state["system_id"],
        profile=state["system_profile"],
        follow_up_questions=state.get("follow_up_questions", []),
        risk_classification=state["risk_classification"],
        retrieved_requirements=state.get("retrieved_requirements", []),
        mapped_controls=state.get("mapped_controls", []),
        gap_analysis=state["gap_analysis"],
        evidence_checklist=state["evidence_checklist"],
        ai_system_card=state["ai_system_card"],
        audit_report=state["audit_report"],
        requires_human_review=True,
        human_review_status="needs_review",
        status="needs_review",
        tool_calls=state.get("tool_calls", []),
    )

