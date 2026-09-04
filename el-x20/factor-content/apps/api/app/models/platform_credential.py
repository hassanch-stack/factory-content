"""PlatformCredential — nunca en columnas planas; encrypted_payload se
cifra/descifra solo dentro de publishers/*, nunca en un router (spec 24)."""
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampedUUIDMixin


class PlatformCredential(TimestampedUUIDMixin, Base):
    __tablename__ = "platform_credentials"

    account_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    platform: Mapped[str] = mapped_column(String(50))
    encrypted_payload: Mapped[str] = mapped_column(String)
    expires_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refreshed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
