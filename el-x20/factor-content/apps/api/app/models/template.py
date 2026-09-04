"""Template — data-driven, versionado (spec sección 8)."""
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampedUUIDMixin


class Template(TimestampedUUIDMixin, Base):
    __tablename__ = "templates"

    name: Mapped[str] = mapped_column(String(255))
    version: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    configuration_json: Mapped[dict] = mapped_column(JSONB)
