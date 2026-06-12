from datetime import datetime

from pydantic import BaseModel, Field


class IncidentCreate(BaseModel):
    system_id: str
    assessment_id: str | None = None
    title: str = Field(min_length=3)
    description: str = Field(min_length=10)
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    owner: str = "AI Operations"
    detected_at: datetime | None = None
    impact_summary: str = ""
    containment_actions: list[str] = Field(default_factory=list)
    regulatory_report_required: bool = False
    regulatory_report_due_at: datetime | None = None


class IncidentUpdate(BaseModel):
    severity: str | None = Field(default=None, pattern="^(low|medium|high|critical)$")
    status: str | None = Field(default=None, pattern="^(reported|triaging|contained|resolved|closed)$")
    owner: str | None = None
    impact_summary: str | None = None
    containment_actions: list[str] | None = None
    root_cause: str | None = None
    corrective_actions: list[str] | None = None
    regulatory_report_required: bool | None = None
    regulatory_report_due_at: datetime | None = None
    regulatory_reported_at: datetime | None = None
    regulatory_report_reference: str | None = None
    resolved_at: datetime | None = None


class IncidentRead(BaseModel):
    id: str
    tenant_id: str
    system_id: str
    assessment_id: str | None = None
    title: str
    description: str
    severity: str
    status: str
    owner: str
    detected_at: datetime
    impact_summary: str = ""
    containment_actions_json: list[str]
    root_cause: str | None = None
    corrective_actions_json: list[str]
    regulatory_report_required: bool
    regulatory_report_due_at: datetime | None = None
    regulatory_reported_at: datetime | None = None
    regulatory_report_reference: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
