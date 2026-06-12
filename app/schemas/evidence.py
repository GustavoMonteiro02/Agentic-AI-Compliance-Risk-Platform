from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EvidenceRecordRead(BaseModel):
    id: str
    assessment_id: str
    name: str
    description: str = ""
    priority: str
    owner: str
    status: str
    file_url: str | None = None
    source_system: str | None = None
    evidence_hash: str | None = None
    collected_at: datetime | None = None
    retention_until: datetime | None = None
    evidence_metadata_json: dict[str, Any] = Field(default_factory=dict)
    due_date: datetime | None = None
    expires_at: datetime | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    review_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EvidenceUpdate(BaseModel):
    status: str = Field(pattern="^(missing|partial|generated|uploaded|approved|rejected)$")
    description: str | None = None
    owner: str | None = None
    file_url: str | None = None
    source_system: str | None = None
    evidence_hash: str | None = None
    collected_at: datetime | None = None
    retention_until: datetime | None = None
    evidence_metadata_json: dict[str, Any] | None = None
    due_date: datetime | None = None
    expires_at: datetime | None = None
    approved_by: str | None = None
    review_notes: str | None = None
