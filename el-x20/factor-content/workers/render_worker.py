"""Worker de la cola 'render' (spec sección 22). Cada tarea:
- tiene job ID único (el propio RenderJob.id, no un ID de Celery separado)
- es idempotente (run_render_job comprueba SUCCEEDED antes de reprocesar)
- tiene retry con backoff y timeout (heredado de la config global de Celery
  + max_retries aquí)
- registra fallos estructurados en RenderJob.error_code/error_message
"""
import logging

from app.core.db import SessionLocal
from app.services.render_service import RenderError, run_render_job
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="workers.render.execute_render_job",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="render",
)
def execute_render_job(self, render_job_id: str) -> str:
    db = SessionLocal()
    try:
        job = run_render_job(db, render_job_id, worker_id=self.request.id or "unknown")
        logger.info(
            "render job completado",
            extra={"job_id": render_job_id, "operation": "render", "status": job.status},
        )
        return str(job.id)
    except RenderError:
        # Error de datos (job/template no encontrado): no tiene sentido
        # reintentar, es un error permanente.
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "render job falló, reintentando",
            extra={"job_id": render_job_id, "operation": "render", "error_code": type(exc).__name__},
        )
        raise self.retry(exc=exc)
    finally:
        db.close()
