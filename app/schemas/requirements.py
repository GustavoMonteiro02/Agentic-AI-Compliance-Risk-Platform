from datetime import datetime

from pydantic import BaseModel


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
