import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.post import Post
from app.schemas.post import PostOut

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.get("", response_model=list[PostOut])
def list_posts(status: str | None = None, account_id: uuid.UUID | None = None, db: Session = Depends(get_db)):
    query = select(Post).order_by(Post.scheduled_at)
    if status:
        query = query.where(Post.status == status)
    if account_id:
        query = query.where(Post.account_id == account_id)
    return list(db.scalars(query))


@router.get("/{post_id}/status", response_model=PostOut)
def get_post_status(post_id: uuid.UUID, db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(404, "Post no encontrado")
    return post


@router.post("/{post_id}/publish", response_model=PostOut)
def force_publish(post_id: uuid.UUID, db: Session = Depends(get_db)):
    """Publicación manual inmediata (fuera del ciclo de polling normal) —
    útil para depuración/operación; sigue pasando por publish_post, así
    que respeta la misma idempotencia y locking que el flujo automático.
    Reutiliza la misma lógica de reunir slides ordenados que el worker."""
    from app.publishers import get_adapter
    from workers.publish_worker import _build_caption, _ordered_media_paths

    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(404, "Post no encontrado")

    media_paths = _ordered_media_paths(db, post.content_item_id)
    if not media_paths:
        raise HTTPException(422, "No hay media renderizada para este content item")

    from app.services import scheduler_service
    try:
        return scheduler_service.publish_post(
            db, post_id, adapter=get_adapter(post.platform),
            media_paths=media_paths, caption=_build_caption(db, post.content_item_id),
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Fallo al publicar: {exc}") from exc
