"""PostEvent — historial de cada transición/intento de un Post."""
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampedUUIDMixin


class PostEvent(TimestampedUUIDMixin, Base):
    __tablename__ = "post_events"

    post_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("posts.id"))
    event_type: Mapped[str] = mapped_column(String(50))  # state_transition|publish_attempt|error
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
