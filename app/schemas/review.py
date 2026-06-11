from pydantic import BaseModel, Field


class ReviewDecision(BaseModel):
    reviewer: str = Field(min_length=2)
    notes: str = Field(default="")
    override_risk_level: str | None = None
    override_justification: str | None = None


class ReviewRead(BaseModel):
    assessment_id: str
    reviewer: str
    status: str
    notes: str


class ReviewQueueItem(BaseModel):
    assessment_id: str
    system_id: str
    system_name: str
    risk_level: str
    status: str
    critical_gap_count: int
    missing_evidence_count: int
    age_hours: float = 0.0
    escalation_level: str = "normal"
    escalation_reason: str | None = None
