"""Account — spec sección 12."""
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampedUUIDMixin


class Account(TimestampedUUIDMixin, Base):
    __tablename__ = "accounts"

    name: Mapped[str] = mapped_column(String(255))
    platform: Mapped[str] = mapped_column(String(50))
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    publishing_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    credential_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
