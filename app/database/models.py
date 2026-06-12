from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database.session import Base


def new_id() -> str:
    return str(uuid4())


class AISystem(Base):
    __tablename__ = "ai_systems"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(120), default="default", index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    business_unit: Mapped[str | None] = mapped_column(String(255))
    owner: Mapped[str | None] = mapped_column(String(255))
    technical_owner: Mapped[str | None] = mapped_column(String(255))
    deployment_status: Mapped[str] = mapped_column(String(80), default="draft")
    users_affected: Mapped[list[str]] = mapped_column(JSON, default=list)
    data_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    model_provider: Mapped[str | None] = mapped_column(String(255))
    model_type: Mapped[str | None] = mapped_column(String(255))
    decision_impact: Mapped[str | None] = mapped_column(String(255))
    autonomy_level: Mapped[str | None] = mapped_column(String(255))
    human_oversight_process: Mapped[str | None] = mapped_column(Text)
    system_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assessments: Mapped[list["RiskAssessment"]] = relationship(back_populates="system")


class AISystemProfile(Base):
    __tablename__ = "ai_system_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(120), default="default", index=True)
    system_id: Mapped[str] = mapped_column(ForeignKey("ai_systems.id"))
    profile_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(120), default="default", index=True)
    system_id: Mapped[str] = mapped_column(ForeignKey("ai_systems.id"))
    risk_level: Mapped[str] = mapped_column(String(80))
    confidence: Mapped[float] = mapped_column(Float)
    risk_factors_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    reasoning_summary: Mapped[str] = mapped_column(Text)
    assessment_json: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(80), default="needs_review")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    system: Mapped[AISystem] = relationship(back_populates="assessments")


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    requirement_code: Mapped[str] = mapped_column(String(255), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MappedControlRecord(Base):
    __tablename__ = "mapped_controls"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("risk_assessments.id"))
    requirement_id: Mapped[str] = mapped_column(String(255))
    control_name: Mapped[str] = mapped_column(String(255))
    control_description: Mapped[str] = mapped_column(Text)
    control_status: Mapped[str] = mapped_column(String(80))
    evidence_needed_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ComplianceGap(Base):
    __tablename__ = "compliance_gaps"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("risk_assessments.id"))
    gap_title: Mapped[str] = mapped_column(String(255))
    gap_description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(80))
    recommended_action: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(80), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RiskRegisterItem(Base):
    __tablename__ = "risk_register_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(120), default="default", index=True)
    assessment_id: Mapped[str] = mapped_column(String, index=True)
    system_id: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(80))
    likelihood: Mapped[str] = mapped_column(String(80), default="medium")
    impact: Mapped[str] = mapped_column(String(80), default="medium")
    owner: Mapped[str] = mapped_column(String(255), default="Compliance")
    status: Mapped[str] = mapped_column(String(80), default="open")
    mitigation_plan: Mapped[str] = mapped_column(Text, default="")
    source_gap: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PolicyException(Base):
    __tablename__ = "policy_exceptions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(120), default="default", index=True)
    assessment_id: Mapped[str] = mapped_column(String, index=True)
    system_id: Mapped[str] = mapped_column(String, index=True)
    requirement_id: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))
    justification: Mapped[str] = mapped_column(Text)
    compensating_controls_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    requested_by: Mapped[str] = mapped_column(String(255))
    approved_by: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(80), default="requested")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AIIncident(Base):
    __tablename__ = "ai_incidents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(120), default="default", index=True)
    system_id: Mapped[str] = mapped_column(String, index=True)
    assessment_id: Mapped[str | None] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(80), default="medium")
    status: Mapped[str] = mapped_column(String(80), default="reported")
    owner: Mapped[str] = mapped_column(String(255), default="AI Operations")
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    impact_summary: Mapped[str] = mapped_column(Text, default="")
    containment_actions_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    root_cause: Mapped[str | None] = mapped_column(Text)
    corrective_actions_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    regulatory_report_required: Mapped[bool] = mapped_column(Boolean, default=False)
    regulatory_report_due_at: Mapped[datetime | None] = mapped_column(DateTime)
    regulatory_reported_at: Mapped[datetime | None] = mapped_column(DateTime)
    regulatory_report_reference: Mapped[str | None] = mapped_column(String(255))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EvidenceItemRecord(Base):
    __tablename__ = "evidence_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("risk_assessments.id"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String(80))
    owner: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(80))
    file_url: Mapped[str | None] = mapped_column(String(500))
    source_system: Mapped[str | None] = mapped_column(String(255))
    evidence_hash: Mapped[str | None] = mapped_column(String(255))
    collected_at: Mapped[datetime | None] = mapped_column(DateTime)
    retention_until: Mapped[datetime | None] = mapped_column(DateTime)
    evidence_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    due_date: Mapped[datetime | None] = mapped_column(DateTime)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    approved_by: Mapped[str | None] = mapped_column(String(255))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    review_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SystemCard(Base):
    __tablename__ = "system_cards"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    system_id: Mapped[str] = mapped_column(ForeignKey("ai_systems.id"))
    assessment_id: Mapped[str] = mapped_column(ForeignKey("risk_assessments.id"))
    content_markdown: Mapped[str] = mapped_column(Text)
    content_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(80), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditReport(Base):
    __tablename__ = "audit_reports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("risk_assessments.id"))
    content_markdown: Mapped[str] = mapped_column(Text)
    content_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(80), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HumanReview(Base):
    __tablename__ = "human_reviews"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("risk_assessments.id"))
    reviewer: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(80))
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("risk_assessments.id"))
    run_type: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(80))
    langsmith_trace_url: Mapped[str | None] = mapped_column(String(500))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    agent_run_id: Mapped[str | None] = mapped_column(ForeignKey("agent_runs.id"))
    assessment_id: Mapped[str] = mapped_column(String)
    tool_name: Mapped[str] = mapped_column(String(255))
    tool_args_json: Mapped[dict] = mapped_column(JSON, default=dict)
    tool_result_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(120), default="default", index=True)
    assessment_id: Mapped[str | None] = mapped_column(String, index=True)
    actor: Mapped[str] = mapped_column(String(255))
    actor_role: Mapped[str] = mapped_column(String(80))
    action: Mapped[str] = mapped_column(String(255))
    resource_type: Mapped[str] = mapped_column(String(120))
    resource_id: Mapped[str | None] = mapped_column(String(255))
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class NotificationEvent(Base):
    __tablename__ = "notification_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(120), default="default", index=True)
    assessment_id: Mapped[str | None] = mapped_column(String, index=True)
    event_type: Mapped[str] = mapped_column(String(120), index=True)
    channel: Mapped[str] = mapped_column(String(80), default="in_app")
    recipient: Mapped[str | None] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(80), default="queued", index=True)
    dedupe_key: Mapped[str] = mapped_column(String(255), index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    assessment_id: Mapped[str | None] = mapped_column(String)
    metric_name: Mapped[str] = mapped_column(String(255))
    score: Mapped[float] = mapped_column(Float)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
