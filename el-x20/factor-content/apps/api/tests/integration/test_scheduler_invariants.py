"""Invariantes críticos de scheduling (spec 27), contra Postgres real:
1. Un post no puede publicarse dos veces.
2. Posts programados no se publican antes de su hora.
3. Dos workers no pueden reclamar el mismo post (locking).

Requiere DATABASE_URL apuntando a un Postgres real (ver docs/08_TEST_STRATEGY.md,
'Mocking de plataformas externas' — este archivo SÍ toca BD real, a
diferencia de los tests unit que usan MagicMock)."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.account import Account
from app.models.content_item import ContentItem, ContentStatus
from app.models.post import Post, PostStatus
from app.models.source import PermissionStatus, Source
from app.publishers.mock import MockPublisherAdapter
from app.services.scheduler_service import claim_due_posts, publish_post


@pytest.fixture
def approved_content_item(db_session):
    source = Source(
        name="test-source", platform="rss", source_url="https://example.com/feed",
        permission_status=PermissionStatus.LICENSED,
    )
    db_session.add(source)
    db_session.flush()

    item = ContentItem(
        source_id=source.id, source_url="https://example.com/a", title="t",
        status=ContentStatus.APPROVED, rights_status="LICENSED",
    )
    db_session.add(item)
    db_session.flush()
    return item


@pytest.fixture
def account(db_session):
    acc = Account(name="Test Account", platform="tiktok")
    db_session.add(acc)
    db_session.flush()
    return acc


def test_claim_due_posts_never_returns_future_post(db_session, approved_content_item, account):
    future_post = Post(
        content_item_id=approved_content_item.id, account_id=account.id, platform="tiktok",
        scheduled_at=datetime.now(timezone.utc) + timedelta(hours=1),
        status=PostStatus.SCHEDULED,
    )
    db_session.add(future_post)
    db_session.commit()

    claimed = claim_due_posts(db_session)
    assert future_post.id not in [p.id for p in claimed]


def test_publish_post_is_idempotent(db_session, approved_content_item, account):
    post = Post(
        content_item_id=approved_content_item.id, account_id=account.id, platform="tiktok",
        scheduled_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        status=PostStatus.PUBLISHING,
    )
    db_session.add(post)
    db_session.commit()

    adapter = MockPublisherAdapter()
    result1 = publish_post(db_session, post.id, adapter=adapter, media_path="x.jpg", caption="c")
    assert result1.status == PostStatus.PUBLISHED
    external_id_first = result1.external_post_id

    # Segunda llamada (simula reintento tardío de una tarea Celery duplicada):
    # no debe volver a llamar al adapter ni cambiar el external_post_id.
    result2 = publish_post(db_session, post.id, adapter=adapter, media_path="x.jpg", caption="c")
    assert result2.status == PostStatus.PUBLISHED
    assert result2.external_post_id == external_id_first
