from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


LEGAL_REVIEW_DISCLAIMER = (
    "This analysis is an initial governance and audit-readiness aid. It is not legal advice "
    "and requires validation by qualified human reviewers."
)


class SystemProfile(BaseModel):
    system_name: str
    use_case: str
    business_unit: str | None = None
    system_owner: str | None = None
    technical_owner: str | None = None
    business_domain: str = "unknown"
    affected_users: list[str] = Field(default_factory=list)
    external_users_affected: bool = False
    data_types: list[str] = Field(default_factory=list)
    model_provider: str | None = None
    model_type: str | None = None
    integrations_tools_used: list[str] = Field(default_factory=list)
    personal_data: bool = False
    sensitive_data: bool = False
    decision_impact: str = "unknown"
    autonomy_level: str = "unknown"
    human_oversight: str = "unknown"
    deployment_status: str = "unknown"
    monitoring_status: str | None = None
    evaluation_status: str | None = None
    security_testing_status: str | None = None
    missing_information: list[str] = Field(default_factory=list)


class FollowUpQuestion(BaseModel):
    field: str
    question: str
    priority: str = "medium"


class UserAnswer(BaseModel):
    field: str
    answer: str


class AssessmentRunRequest(BaseModel):
    user_answers: list[UserAnswer] = Field(default_factory=list)
    additional_context: dict[str, Any] = Field(default_factory=dict)


class RiskClassification(BaseModel):
    risk_level: str
    confidence: float = Field(ge=0, le=1)
    risk_factors: list[str] = Field(default_factory=list)
    reasoning_summary: str
    requires_human_review: bool = True
    requires_additional_information: bool = False


class RetrievedRequirement(BaseModel):
    requirement_id: str
    title: str
    source: str
    summary: str
    relevance: str = "medium"


class MappedControl(BaseModel):
    requirement_id: str
    requirement: str
    mapped_control: str
    evidence_needed: list[str] = Field(default_factory=list)
    control_status: str = "unknown"


class GapItem(BaseModel):
    gap: str
    risk: str
    recommended_action: str


class GapAnalysis(BaseModel):
    overall_status: str
    critical_gaps: list[GapItem] = Field(default_factory=list)
    medium_gaps: list[GapItem] = Field(default_factory=list)
    low_gaps: list[GapItem] = Field(default_factory=list)
    priority_actions: list[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    evidence: str
    status: str = "missing"
    priority: str = "medium"
    owner: str = "AI Engineering"


class GeneratedDocument(BaseModel):
    title: str
    content_markdown: str
    content_json: dict[str, Any] = Field(default_factory=dict)
    status: str = "draft"


class GovernanceAssessment(BaseModel):
    id: str
    system_id: str
    profile: SystemProfile
    follow_up_questions: list[FollowUpQuestion] = Field(default_factory=list)
    risk_classification: RiskClassification
    retrieved_requirements: list[RetrievedRequirement] = Field(default_factory=list)
    mapped_controls: list[MappedControl] = Field(default_factory=list)
    gap_analysis: GapAnalysis
    evidence_checklist: list[EvidenceItem] = Field(default_factory=list)
    ai_system_card: GeneratedDocument
    audit_report: GeneratedDocument
    requires_human_review: bool = True
    human_review_status: str = "needs_review"
    human_review_notes: str | None = None
    status: str = "needs_review"
    disclaimer: str = LEGAL_REVIEW_DISCLAIMER
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
