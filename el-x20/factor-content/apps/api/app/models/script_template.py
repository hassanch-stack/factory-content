"""ScriptTemplate — la plantilla de GUION que el operador proporciona
(distinta de Template, que es la plantilla VISUAL de composición de foto).
Define la estructura que la IA debe seguir al reescribir: secciones,
límites de longitud, cuántos hashtags/keywords generar, tono, etc."""
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampedUUIDMixin


class ScriptTemplate(TimestampedUUIDMixin, Base):
    __tablename__ = "script_templates"

    name: Mapped[str] = mapped_column(String(255))
    version: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    configuration_json: Mapped[dict] = mapped_column(JSONB)
