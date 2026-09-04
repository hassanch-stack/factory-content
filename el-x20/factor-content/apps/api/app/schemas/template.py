import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TemplateCreate(BaseModel):
    name: str
    configuration_json: dict  # se valida contra TemplateConfiguration en el router


class TemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    version: int
    active: bool
    configuration_json: dict
    created_at: datetime
    updated_at: datetime


class RenderJobCreate(BaseModel):
    content_item_id: uuid.UUID
    template_id: uuid.UUID
    input_asset_id: uuid.UUID
    slide_index: int = 0


class RenderJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content_item_id: uuid.UUID
    template_id: uuid.UUID
    template_version: int
    slide_index: int
    status: str
    progress: int
    error_code: str | None
    error_message: str | None
