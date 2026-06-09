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

