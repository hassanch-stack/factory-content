"""Entrypoint de Celery. Las 7 colas del spec (sección 21): radar, import,
render, ai, publish, analytics, cleanup. Cada tarea real vive en su propio
módulo *_worker.py e importa directamente app/services (sin duplicar lógica,
ver ADR 0001)."""
from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "factor_content",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,          # no perder el job si el worker muere a mitad
    worker_prefetch_multiplier=1,  # evita que un worker acapare jobs largos de render
    task_default_retry_delay=30,
    task_time_limit=1800,          # 30 min hard timeout, ningún job corre sin límite
)

celery_app.autodiscover_tasks(["workers"])

from workers.beat_schedule import BEAT_SCHEDULE  # noqa: E402
celery_app.conf.beat_schedule = BEAT_SCHEDULE


@celery_app.task(name="workers.ping")
def ping() -> str:
    """Tarea de humo para Phase 0 — confirma que broker/worker funcionan
    antes de añadir lógica real en Phase 1+."""
    return "pong"
