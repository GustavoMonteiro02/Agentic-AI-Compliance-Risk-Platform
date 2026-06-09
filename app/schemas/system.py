from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AISystemCreate(BaseModel):
    name: str = Field(min_length=2)
    description: str = Field(min_length=10)
    business_unit: str | None = None
    owner: str | None = None
    technical_owner: str | None = None
    deployment_status: str = "draft"
    users_affected: list[str] = Field(default_factory=list)
    data_types: list[str] = Field(default_factory=list)
    model_provider: str | None = None
    model_type: str | None = None
    decision_impact: str | None = None
    autonomy_level: str | None = None
    human_oversight_process: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AISystemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    business_unit: str | None = None
    owner: str | None = None
    technical_owner: str | None = None
    deployment_status: str | None = None
    users_affected: list[str] | None = None
    data_types: list[str] | None = None
    model_provider: str | None = None
    model_type: str | None = None
    decision_impact: str | None = None
    autonomy_level: str | None = None
    human_oversight_process: str | None = None
    metadata: dict[str, Any] | None = None


class AISystemRead(AISystemCreate):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

