"""Modelo Source — spec sección 5.1."""
import enum

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampedUUIDMixin


class PermissionStatus(str, enum.Enum):
    UNKNOWN = "UNKNOWN"
    AUTHORIZED = "AUTHORIZED"
    LICENSED = "LICENSED"
    PUBLIC_DOMAIN = "PUBLIC_DOMAIN"
    PLATFORM_SUPPORTED = "PLATFORM_SUPPORTED"
    RESTRICTED = "RESTRICTED"
    REJECTED = "REJECTED"


class Source(TimestampedUUIDMixin, Base):
    __tablename__ = "sources"

    name: Mapped[str] = mapped_column(String(255))
    platform: Mapped[str] = mapped_column(String(50))
    source_url: Mapped[str] = mapped_column(String(1024))
    external_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    country: Mapped[str | None] = mapped_column(String(10), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)

    # Regla dura (spec 5.1): nunca se procesa automáticamente una fuente
    # UNKNOWN sin aprobación explícita del operador.
    permission_status: Mapped[PermissionStatus] = mapped_column(
        String(30), default=PermissionStatus.UNKNOWN
    )

    active: Mapped[bool] = mapped_column(Boolean, default=True)
    polling_interval: Mapped[int] = mapped_column(Integer, default=300)  # segundos
    last_checked_at: Mapped[str | None] = mapped_column(nullable=True)

    def can_be_auto_processed(self) -> bool:
        """Un Radar nunca debe llamar a esto sin antes chequear esta regla."""
        return self.active and self.permission_status not in (
            PermissionStatus.UNKNOWN,
            PermissionStatus.REJECTED,
            PermissionStatus.RESTRICTED,
        )
