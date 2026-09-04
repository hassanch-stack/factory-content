"""RenderJob — spec sección 9. La idempotencia se garantiza por
(content_item_id, template_id, template_version, slide_index), nunca por
reintento ciego.

slide_index: soporte de carrusel — un ContentItem puede necesitar varios
slides (ej. slide 0 = hook, slide 1 = cuerpo con burbujas), cada uno con
su propio Template. publish_worker los agrupa por content_item_id y los
publica en orden de slide_index."""
import enum

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampedUUIDMixin


class RenderJobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RenderJob(TimestampedUUIDMixin, Base):
    __tablename__ = "render_jobs"

    content_item_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("content_items.id"))
    template_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("templates.id"))
    template_version: Mapped[int] = mapped_column(Integer)
    slide_index: Mapped[int] = mapped_column(Integer, default=0)
    input_asset_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("media_assets.id"))
    output_asset_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_assets.id"), nullable=True
    )
    status: Mapped[RenderJobStatus] = mapped_column(String(20), default=RenderJobStatus.QUEUED)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[str | None] = mapped_column(nullable=True)
    completed_at: Mapped[str | None] = mapped_column(nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
