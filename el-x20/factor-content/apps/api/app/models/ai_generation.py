"""AIGeneration — spec sección 10, ampliado tras el pivote: ya no es solo
metadata corta, es la reescritura completa (hook/guion/CTA/título/hashtags/
keywords/estructura). Reglas del spec que siguen vigentes sin excepción:
- la IA NUNCA inventa hechos, citas ni cifras
- todo output es editable por el usuario
- cada generación queda versionada (model + prompt_version)"""
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampedUUIDMixin


class AIGeneration(TimestampedUUIDMixin, Base):
    __tablename__ = "ai_generations"

    source_content_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("content_items.id"))
    script_template_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("script_templates.id"))
    model: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(50))
    output_json: Mapped[dict] = mapped_column(JSONB)
    edited_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
