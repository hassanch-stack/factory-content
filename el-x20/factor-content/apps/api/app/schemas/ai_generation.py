import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ScriptOutput(BaseModel):
    """Forma validada de lo que la IA debe devolver. Los nombres de
    sections.role coinciden con lo pedido por el ScriptTemplate usado.
    Una sección con repeat=True en la plantilla debe devolverse aquí como
    lista de N strings (para las bubble_lists de la plantilla visual);
    una sección normal se devuelve como un único string."""
    hook: str
    sections: dict[str, str | list[str]] = Field(default_factory=dict)  # role -> texto o lista de beats
    cta: str
    title: str
    hashtags: list[str]
    keywords: list[str]


class AIGenerationCreate(BaseModel):
    content_item_id: uuid.UUID
    script_template_id: uuid.UUID


class AIGenerationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_content_id: uuid.UUID
    script_template_id: uuid.UUID
    model: str
    prompt_version: str
    output_json: dict
    edited_by_user: bool
    created_at: datetime


class AIGenerationEdit(BaseModel):
    output_json: dict
