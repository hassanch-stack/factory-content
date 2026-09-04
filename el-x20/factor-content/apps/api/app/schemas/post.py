import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ScheduleCreate(BaseModel):
    content_item_id: uuid.UUID
    account_id: uuid.UUID
    platform: str
    scheduled_at: datetime


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content_item_id: uuid.UUID
    account_id: uuid.UUID
    platform: str
    scheduled_at: datetime
    status: str
    external_post_id: str | None
    published_at: datetime | None
    failure_reason: str | None
    retry_count: int
