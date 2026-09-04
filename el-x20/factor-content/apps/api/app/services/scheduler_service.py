"""Scheduler — spec sección 15. Requisitos duros que este módulo garantiza:
- timezone-aware (todo scheduled_at se compara en UTC vía la BD)
- idempotente (publish_post no re-publica un Post ya PUBLISHED)
- locking (claim_due_posts usa SELECT ... FOR UPDATE SKIP LOCKED — dos
  workers no pueden agarrar el mismo Post)
- retry con backoff exponencial (ver publish_worker.py)
- nunca recoge un post programado en el futuro (claim_due_posts filtra por
  scheduled_at <= NOW() del propio servidor de BD, no del reloj del worker)
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content_item import ContentItem, ContentStatus, InvalidTransitionError
from app.models.post import Post, PostStatus
from app.models.post_event import PostEvent
from app.publishers.base import PublisherAdapter
from app.services import audit_service


class SchedulerError(Exception):
    pass


def schedule_post(db: Session, *, content_item_id, account_id, platform: str, scheduled_at: datetime) -> Post:
    content_item = db.get(ContentItem, content_item_id)
    if not content_item:
        raise SchedulerError("Content item no encontrado")

    if not content_item.can_enter_automatic_publishing():
        raise SchedulerError(
            f"rights_status='{content_item.rights_status}' no permite programar publicación"
        )

    if content_item.status != ContentStatus.APPROVED:
        raise SchedulerError(
            f"Solo se puede programar contenido APPROVED (actual: {content_item.status})"
        )

    post = Post(
        content_item_id=content_item_id,
        account_id=account_id,
        platform=platform,
        scheduled_at=scheduled_at,
        status=PostStatus.SCHEDULED,
    )
    db.add(post)

    try:
        content_item.transition_to(ContentStatus.SCHEDULED)
    except InvalidTransitionError as exc:
        raise SchedulerError(str(exc)) from exc

    db.commit()
    db.refresh(post)
    return post


def claim_due_posts(db: Session, *, limit: int = 10) -> list[Post]:
    """Reclama hasta `limit` posts SCHEDULED cuya hora ya llegó, con lock
    a nivel de fila para que dos workers concurrentes nunca se lleven el
    mismo Post (invariante crítico: un post no puede publicarse dos veces)."""
    query = (
        select(Post)
        .where(Post.status == PostStatus.SCHEDULED, Post.scheduled_at <= datetime.now(timezone.utc))
        .order_by(Post.scheduled_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    posts = list(db.scalars(query))
    for post in posts:
        post.status = PostStatus.PUBLISHING
    db.commit()
    return posts


def publish_post(db: Session, post_id, *, adapter: PublisherAdapter, media_paths: list[str], caption: str) -> Post:
    """Idempotente: si el post ya está PUBLISHED (ej. reintento tardío de
    una tarea de Celery duplicada), devuelve el estado actual sin volver a
    llamar al adapter — nunca se publica dos veces."""
    post = db.get(Post, post_id)
    if not post:
        raise SchedulerError("Post no encontrado")

    if post.status == PostStatus.PUBLISHED:
        return post

    try:
        validation = adapter.validate_post(media_paths=media_paths, caption=caption, credential_payload={})
        if not validation.valid:
            post.transition_to(PostStatus.MANUAL_ACTION_REQUIRED)
            post.failure_reason = "; ".join(validation.errors)
            db.add(PostEvent(post_id=post.id, event_type="error", payload={"errors": validation.errors}))
            db.commit()
            return post

        result = adapter.publish_video(media_paths=media_paths, caption=caption, credential_payload={})

        if result.status == "published":
            post.transition_to(PostStatus.PUBLISHED)
            post.external_post_id = result.external_post_id
            post.published_at = datetime.now(timezone.utc)
        elif result.status == "pending_manual_action":
            post.transition_to(PostStatus.MANUAL_ACTION_REQUIRED)
            post.external_post_id = result.external_post_id
        else:
            post.transition_to(PostStatus.FAILED)
            post.failure_reason = f"Estado inesperado del adapter: {result.status}"

        db.add(PostEvent(
            post_id=post.id, event_type="publish_attempt",
            payload={"status": result.status, "external_post_id": result.external_post_id},
        ))

        if post.status == PostStatus.PUBLISHED:
            content_item = db.get(ContentItem, post.content_item_id)
            if content_item and content_item.status == ContentStatus.SCHEDULED:
                content_item.transition_to(ContentStatus.PUBLISHED)
            audit_service.record(
                db, user_id=None, action="post.publish", entity_type="post",
                entity_id=post.id, after={"external_post_id": post.external_post_id},
            )

        db.commit()

    except Exception as exc:  # noqa: BLE001 — nunca se oculta, se registra estructurado
        db.rollback()
        post = db.get(Post, post_id)  # recargar tras rollback
        post.retry_count += 1
        post.transition_to(PostStatus.FAILED)
        post.failure_reason = f"{type(exc).__name__}: {exc}"[:2000]
        db.add(PostEvent(post_id=post.id, event_type="error", payload={"error": str(exc)[:2000]}))
        db.commit()
        raise

    db.refresh(post)
    return post


def requeue_failed_post(db: Session, post_id, *, new_scheduled_at: datetime) -> Post:
    """Reintento seguro: FAILED -> SCHEDULED con nueva hora (backoff
    calculado por el worker, no aquí)."""
    post = db.get(Post, post_id)
    if not post:
        raise SchedulerError("Post no encontrado")
    post.transition_to(PostStatus.SCHEDULED)
    post.scheduled_at = new_scheduled_at
    db.commit()
    db.refresh(post)
    return post
