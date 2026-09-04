"""Registro de cada polling del Radar sobre una Source (spec 5.1/22)."""
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampedUUIDMixin


class SourceCheck(TimestampedUUIDMixin, Base):
    __tablename__ = "source_checks"

    source_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id"))
    checked_at: Mapped[str] = mapped_column()
    items_found: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="ok")
