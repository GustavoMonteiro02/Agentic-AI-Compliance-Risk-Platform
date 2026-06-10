from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditEventRead(BaseModel):
    id: str
    assessment_id: str | None = None
    actor: str
    actor_role: str
    action: str
    resource_type: str
    resource_id: str | None = None
    details_json: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}
