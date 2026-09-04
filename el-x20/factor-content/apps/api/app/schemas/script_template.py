import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ScriptTemplateCreate(BaseModel):
    name: str
    configuration_json: dict  # validado contra ScriptTemplateConfiguration


class ScriptTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    version: int
    active: bool
    configuration_json: dict
    created_at: datetime
    updated_at: datetime
