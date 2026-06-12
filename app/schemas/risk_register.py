from datetime import datetime

from pydantic import BaseModel, Field


class RiskRegisterItemRead(BaseModel):
    id: str
    tenant_id: str
    assessment_id: str
    system_id: str
    title: str
    description: str
    severity: str
    likelihood: str
    impact: str
    owner: str
    status: str
    mitigation_plan: str = ""
    source_gap: str | None = None
    due_date: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RiskRegisterItemUpdate(BaseModel):
    owner: str | None = None
    status: str | None = Field(default=None, pattern="^(open|mitigating|accepted|closed)$")
    likelihood: str | None = Field(default=None, pattern="^(low|medium|high)$")
    impact: str | None = Field(default=None, pattern="^(low|medium|high)$")
    mitigation_plan: str | None = None
    due_date: datetime | None = None


class PolicyExceptionCreate(BaseModel):
    assessment_id: str
    requirement_id: str | None = None
    title: str = Field(min_length=3)
    justification: str = Field(min_length=10)
    compensating_controls: list[str] = Field(default_factory=list)
    requested_by: str = Field(min_length=2)
    expires_at: datetime | None = None


class PolicyExceptionUpdate(BaseModel):
    status: str = Field(pattern="^(requested|approved|rejected|expired)$")
    approved_by: str | None = None
    compensating_controls: list[str] | None = None
    expires_at: datetime | None = None


class PolicyExceptionRead(BaseModel):
    id: str
    tenant_id: str
    assessment_id: str
    system_id: str
    requirement_id: str | None = None
    title: str
    justification: str
    compensating_controls_json: list[str]
    requested_by: str
    approved_by: str | None = None
    status: str
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PolicyExceptionQueueItem(BaseModel):
    id: str
    tenant_id: str
    assessment_id: str
    system_id: str
    requirement_id: str | None = None
    title: str
    status: str
    approved_by: str | None = None
    expires_at: datetime | None = None
    days_until_expiry: int | None = None
    expiry_state: str
    compensating_control_count: int = 0
    action_required: str
