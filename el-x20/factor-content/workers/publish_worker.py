"""Worker de la cola 'publish' (spec 22): poll de schedules, lock, valida,
publica, guarda external_id, monitorea estado. Backoff exponencial en
reintentos — nunca reintento agresivo contra límites de tasa de plataforma.

Soporta carrusel: si un content_item tiene varios RenderJob SUCCEEDED
(uno por slide_index), se publican todos juntos en el orden correcto
(slide 0 = hook, slide 1 = cuerpo, etc.)."""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.db import SessionLocal
from app.models.ai_generation import AIGeneration
from app.models.media_asset import MediaAsset
from app.models.post import Post, PostStatus
from app.models.render_job import RenderJob, RenderJobStatus
from app.publishers import get_adapter
from app.services.scheduler_service import claim_due_posts, publish_post, requeue_failed_post
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)

_BACKOFF_MINUTES = [1, 5, 15, 60]  # 4 reintentos con backoff creciente


@celery_app.task(name="workers.publish.poll_and_publish", queue="publish")
def poll_and_publish() -> int:
    """Tarea periódica (celery beat) — reclama posts vencidos y encola su
    publicación individual. Separar 'reclamar' de 'publicar' en dos tareas
    evita que un timeout largo de red bloquee el reclamado de los demás."""
    db = SessionLocal()
    try:
        posts = claim_due_posts(db, limit=20)
        for post in posts:
            execute_publish.delay(str(post.id))
        return len(posts)
    finally:
        db.close()


def _ordered_media_paths(db, content_item_id) -> list[str]:
    """Reúne los outputs de todos los RenderJob SUCCEEDED de este content
    item, ordenados por slide_index — un solo elemento para post simple,
    varios para carrusel (hook + cuerpo, etc.)."""
    jobs = db.scalars(
        select(RenderJob)
        .where(RenderJob.content_item_id == content_item_id, RenderJob.status == RenderJobStatus.SUCCEEDED)
        .order_by(RenderJob.slide_index)
    )
    paths = []
    for job in jobs:
        if job.output_asset_id:
            asset = db.get(MediaAsset, job.output_asset_id)
            if asset:
                paths.append(asset.storage_key)
    return paths


def _build_caption(db, content_item_id) -> str:
    """Patrón 'title_plus_hashtags' observado en el ejemplo del operador:
    título/hook + hashtags. Otros patrones se añaden aquí si el
    ScriptTemplate.configuration_json.caption_pattern lo pide."""
    generation = db.scalar(
        select(AIGeneration)
        .where(AIGeneration.source_content_id == content_item_id)
        .order_by(AIGeneration.created_at.desc())
    )
    if not generation:
        return ""
    output = generation.output_json
    title = output.get("title") or output.get("hook", "")
    hashtags = " ".join(output.get("hashtags", []))
    return f"{title}\n\n{hashtags}".strip()


@celery_app.task(name="workers.publish.execute_publish", bind=True, queue="publish")
def execute_publish(self, post_id: str) -> str:
    db = SessionLocal()
    try:
        post = db.get(Post, post_id)
        if not post:
            logger.error("post no encontrado", extra={"job_id": post_id, "operation": "publish"})
            return "not_found"

        media_paths = _ordered_media_paths(db, post.content_item_id)
        if not media_paths:
            logger.error("sin media renderizada", extra={"job_id": post_id, "operation": "publish"})
            return "no_media"

        adapter = get_adapter(post.platform)
        caption = _build_caption(db, post.content_item_id)

        try:
            result_post = publish_post(
                db, post_id, adapter=adapter, media_paths=media_paths, caption=caption
            )
            logger.info(
                "post publicado", extra={"job_id": post_id, "operation": "publish", "status": result_post.status},
            )
            return result_post.status
        except Exception as exc:  # noqa: BLE001
            post = db.get(Post, post_id)
            if post.status == PostStatus.FAILED and post.retry_count <= len(_BACKOFF_MINUTES):
                delay = _BACKOFF_MINUTES[min(post.retry_count - 1, len(_BACKOFF_MINUTES) - 1)]
                new_time = datetime.now(timezone.utc) + timedelta(minutes=delay)
                requeue_failed_post(db, post_id, new_scheduled_at=new_time)
                logger.warning(
                    "post reprogramado con backoff",
                    extra={"job_id": post_id, "operation": "publish", "duration": delay},
                )
            else:
                logger.error(
                    "post agotó reintentos, requiere acción manual",
                    extra={"job_id": post_id, "operation": "publish", "error_code": type(exc).__name__},
                )
            return "failed"
    finally:
        db.close()
