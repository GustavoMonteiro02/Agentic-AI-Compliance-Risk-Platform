from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
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


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    assessment_id: Mapped[str | None] = mapped_column(String)
    metric_name: Mapped[str] = mapped_column(String(255))
    score: Mapped[float] = mapped_column(Float)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
