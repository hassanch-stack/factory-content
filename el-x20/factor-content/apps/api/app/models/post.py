"""Post — spec sección 15. Máquina de estados propia (distinta de la de
ContentItem): un ContentItem puede tener varios Posts (una pieza puede
publicarse en varias cuentas/plataformas)."""
import enum

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampedUUIDMixin


class PostStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    MANUAL_ACTION_REQUIRED = "MANUAL_ACTION_REQUIRED"


VALID_POST_TRANSITIONS: dict[PostStatus, set[PostStatus]] = {
    PostStatus.DRAFT: {PostStatus.SCHEDULED, PostStatus.CANCELLED},
    PostStatus.SCHEDULED: {PostStatus.PUBLISHING, PostStatus.CANCELLED},
    PostStatus.PUBLISHING: {
        PostStatus.PUBLISHED, PostStatus.FAILED, PostStatus.MANUAL_ACTION_REQUIRED,
    },
    PostStatus.PUBLISHED: set(),  # terminal — nunca se revierte un post ya publicado
    PostStatus.FAILED: {PostStatus.SCHEDULED, PostStatus.CANCELLED},
    PostStatus.CANCELLED: set(),
    PostStatus.MANUAL_ACTION_REQUIRED: {PostStatus.SCHEDULED, PostStatus.CANCELLED},
}


class InvalidPostTransitionError(Exception):
    pass


class Post(TimestampedUUIDMixin, Base):
    __tablename__ = "posts"

    content_item_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("content_items.id"))
    account_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    platform: Mapped[str] = mapped_column(String(50))
    scheduled_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    status: Mapped[PostStatus] = mapped_column(String(30), default=PostStatus.DRAFT)
    external_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    def transition_to(self, new_status: PostStatus) -> None:
        allowed = VALID_POST_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidPostTransitionError(
                f"No se puede pasar de {self.status} a {new_status}. Válidas: {allowed}"
            )
        self.status = new_status
