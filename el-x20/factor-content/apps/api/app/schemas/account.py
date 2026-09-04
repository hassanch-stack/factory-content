import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AccountCreate(BaseModel):
    name: str
    platform: str
    username: str | None = None
    timezone: str = "UTC"
    publishing_enabled: bool = False


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    platform: str
    username: str | None
    timezone: str
    active: bool
    publishing_enabled: bool
    created_at: datetime
