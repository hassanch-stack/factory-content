import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.source import PermissionStatus


class SourceCreate(BaseModel):
    name: str
    platform: str
    source_url: str
    external_identifier: str | None = None
    category: str | None = None
    language: str | None = None
    country: str | None = None
    priority: int = 0
    permission_status: PermissionStatus = PermissionStatus.UNKNOWN
    polling_interval: int = 300


class SourceUpdate(BaseModel):
    name: str | None = None
    priority: int | None = None
    permission_status: PermissionStatus | None = None
    active: bool | None = None
    polling_interval: int | None = None


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    platform: str
    source_url: str
    category: str | None
    language: str | None
    country: str | None
    priority: int
    permission_status: PermissionStatus
    active: bool
    polling_interval: int
    created_at: datetime
    updated_at: datetime
