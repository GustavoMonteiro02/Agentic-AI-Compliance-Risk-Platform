from typing import Any, TypedDict


class GovernanceAssessmentState(TypedDict, total=False):
    assessment_id: str
    system_id: str
    raw_user_description: str
    follow_up_questions: list[dict[str, Any]]
    user_answers: list[dict[str, Any]]
    system_profile: dict[str, Any]
    missing_information: list[str]
    risk_classification: dict[str, Any]
    retrieved_requirements: list[dict[str, Any]]
    mapped_controls: list[dict[str, Any]]
    gap_analysis: dict[str, Any]
    evidence_checklist: list[dict[str, Any]]
    ai_system_card: dict[str, Any]
    audit_report: dict[str, Any]
    requires_human_review: bool
    human_review_status: str | None
    human_review_notes: str | None
    tool_calls: list[dict[str, Any]]
    errors: list[dict[str, Any]]
    status: str

