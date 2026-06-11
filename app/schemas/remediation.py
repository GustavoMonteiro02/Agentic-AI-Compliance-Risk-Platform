from datetime import datetime

from pydantic import BaseModel, Field


class RemediationAction(BaseModel):
    title: str
    description: str
    priority: str = Field(pattern="^(critical|high|medium|low)$")
    owner: str
    due_date: datetime
    source: str
    status: str = "open"


class RemediationPlan(BaseModel):
    assessment_id: str
    system_id: str
    overall_priority: str = Field(pattern="^(critical|high|medium|low)$")
    actions: list[RemediationAction]
    evidence_gaps: int
    critical_gap_count: int
    medium_gap_count: int
