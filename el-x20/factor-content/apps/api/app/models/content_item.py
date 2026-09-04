"""Modelo ContentItem con máquina de estados — spec sección 5.2."""
import enum

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampedUUIDMixin


class ContentStatus(str, enum.Enum):
    DISCOVERED = "DISCOVERED"
    SELECTED = "SELECTED"
    IMPORTING = "IMPORTING"
    IMPORTED = "IMPORTED"
    PROCESSING = "PROCESSING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COPYRIGHT_REVIEW = "COPYRIGHT_REVIEW"
    SCHEDULED = "SCHEDULED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


# Transiciones válidas. Cualquier transición fuera de este mapa se rechaza
# (invariante crítico: "APPROVED no puede volverse REJECTED por accidente").
VALID_TRANSITIONS: dict[ContentStatus, set[ContentStatus]] = {
    ContentStatus.DISCOVERED: {ContentStatus.SELECTED, ContentStatus.ARCHIVED},
    ContentStatus.SELECTED: {ContentStatus.IMPORTING, ContentStatus.ARCHIVED},
    ContentStatus.IMPORTING: {ContentStatus.IMPORTED, ContentStatus.FAILED},
    ContentStatus.IMPORTED: {ContentStatus.PROCESSING, ContentStatus.FAILED},
    ContentStatus.PROCESSING: {ContentStatus.READY_FOR_REVIEW, ContentStatus.FAILED},
    ContentStatus.READY_FOR_REVIEW: {
        ContentStatus.APPROVED, ContentStatus.REJECTED, ContentStatus.COPYRIGHT_REVIEW,
        ContentStatus.PROCESSING,
    },
    ContentStatus.APPROVED: {ContentStatus.SCHEDULED, ContentStatus.ARCHIVED},
    ContentStatus.REJECTED: {ContentStatus.ARCHIVED},
    ContentStatus.COPYRIGHT_REVIEW: {
        ContentStatus.READY_FOR_REVIEW, ContentStatus.REJECTED, ContentStatus.ARCHIVED,
    },
    ContentStatus.SCHEDULED: {ContentStatus.PUBLISHED, ContentStatus.FAILED, ContentStatus.APPROVED},
    ContentStatus.PUBLISHED: {ContentStatus.ARCHIVED},
    ContentStatus.FAILED: {ContentStatus.PROCESSING, ContentStatus.ARCHIVED},
    ContentStatus.ARCHIVED: set(),
}


class InvalidTransitionError(Exception):
    pass


class ContentItem(TimestampedUUIDMixin, Base):
    __tablename__ = "content_items"

    source_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id"))
    source_url: Mapped[str] = mapped_column(String(1024))
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    published_at: Mapped[str | None] = mapped_column(nullable=True)
    discovered_at: Mapped[str | None] = mapped_column(nullable=True)
    factor_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    status: Mapped[ContentStatus] = mapped_column(String(30), default=ContentStatus.DISCOVERED)
    rights_status: Mapped[str] = mapped_column(String(30), default="UNKNOWN")
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    def transition_to(self, new_status: ContentStatus) -> None:
        # La columna se mantiene como VARCHAR por compatibilidad con las
        # migraciones existentes; tras recargar desde PostgreSQL puede llegar
        # como str. Normalizarlo conserva la máquina de estados fiable.
        current_status = ContentStatus(self.status)
        allowed = VALID_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            raise InvalidTransitionError(
                f"No se puede pasar de {current_status} a {new_status}. "
                f"Transiciones válidas: {allowed}"
            )
        self.status = new_status

    def can_enter_automatic_publishing(self) -> bool:
        """Invariante: contenido sin rights_status aceptable no entra a
        publicación automática (spec, sección 27)."""
        return self.rights_status in {"AUTHORIZED", "LICENSED", "PUBLIC_DOMAIN", "PLATFORM_SUPPORTED"}
