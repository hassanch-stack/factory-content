"""Worker de la cola 'analytics' (spec 22): recolecta métricas en los
intervalos configurables (15m/1h/6h/24h/48h), evitando llamadas excesivas
a las APIs de plataforma."""
import logging

from app.core.db import SessionLocal
from app.publishers import get_adapter
from app.services.analytics_service import collect_metrics_for_post, posts_due_for_collection
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.analytics.collect_due_metrics", queue="analytics")
def collect_due_metrics() -> int:
    db = SessionLocal()
    try:
        posts = posts_due_for_collection(db)
        for post in posts:
            try:
                adapter = get_adapter(post.platform)
                collect_metrics_for_post(db, post.id, adapter=adapter)
            except Exception as exc:  # noqa: BLE001 — un fallo de un post no detiene el resto
                logger.error(
                    "fallo recolectando métricas",
                    extra={"job_id": str(post.id), "operation": "analytics", "error_code": type(exc).__name__},
                )
        return len(posts)
    finally:
        db.close()
