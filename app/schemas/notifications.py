from datetime import datetime
from typing import Any

from pydantic import BaseModel


class NotificationEventRead(BaseModel):
    id: str
    tenant_id: str
    assessment_id: str | None = None
    event_type: str
    channel: str
    recipient: str | None = None
    subject: str
    message: str
    status: str
    dedupe_key: str
    payload_json: dict[str, Any]
    created_at: datetime
    delivered_at: datetime | None = None

    model_config = {"from_attributes": True}
