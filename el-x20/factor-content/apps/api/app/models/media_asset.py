"""MediaAsset — nunca binarios en Postgres, solo referencia al storage_key
(spec sección 6)."""
from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampedUUIDMixin


class MediaAsset(TimestampedUUIDMixin, Base):
    __tablename__ = "media_assets"

    content_item_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("content_items.id"))
    storage_key: Mapped[str] = mapped_column(String(1024))
    asset_type: Mapped[str] = mapped_column(String(30))  # original|working|rendered|thumbnail|subtitle
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
