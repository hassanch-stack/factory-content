"""PostMetrics — spec sección 16. raw_platform_data separado de las
columnas normalizadas: el dashboard usa las normalizadas, pero el dato
crudo de cada plataforma nunca se pierde ni se mezcla."""
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampedUUIDMixin


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PostMetrics(TimestampedUUIDMixin, Base):
    __tablename__ = "post_metrics"

    post_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("posts.id"))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    views: Mapped[int] = mapped_column(BigInteger, default=0)
    likes: Mapped[int] = mapped_column(BigInteger, default=0)
    comments: Mapped[int] = mapped_column(BigInteger, default=0)
    shares: Mapped[int] = mapped_column(BigInteger, default=0)
    saves: Mapped[int] = mapped_column(BigInteger, default=0)
    watch_time_ms: Mapped[int] = mapped_column(BigInteger, default=0)
    completion_rate: Mapped[float] = mapped_column(Float, default=0.0)
    followers_gained: Mapped[int] = mapped_column(Integer, default=0)
    raw_platform_data: Mapped[dict] = mapped_column(JSONB, default=dict)
