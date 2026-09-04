import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.content_item import ContentStatus


class ContentItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: uuid.UUID
    title: str | None
    category: str | None
    language: str | None
    factor_score: int
    status: ContentStatus
    rights_status: str
    created_at: datetime
    updated_at: datetime


class ManualImportOut(ContentItemOut):
    """Respuesta de una carga manual, con los datos del archivo aceptado."""

    media_asset_id: uuid.UUID
    mime_type: str
    width: int
    height: int
    file_size: int


class MediaAssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content_item_id: uuid.UUID
    asset_type: str
    mime_type: str | None
    width: int | None
    height: int | None
    file_size: int | None
    created_at: datetime


class ContentItemTransition(BaseModel):
    new_status: ContentStatus
    reason: str | None = None
