from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RequirementRead(BaseModel):
    id: str
    requirement_code: str
    title: str
    description: str
    source: str
    category: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RequirementSearchResult(BaseModel):
    requirement_id: str
    title: str
    source: str
    category: str
    summary: str
    relevance: str = "medium"
    source_url: str | None = None
    jurisdiction: str | None = None
    document_type: str | None = None
    authority: str | None = None
    locator: str | None = None
    content_hash: str | None = None
    tags: list[str] = Field(default_factory=list)
    retriever: str | None = None
    score: float | None = None
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    citation: dict[str, Any] = Field(default_factory=dict)
