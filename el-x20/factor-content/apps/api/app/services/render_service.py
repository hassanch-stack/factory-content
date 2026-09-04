"""Orquestación de un render de FOTO: descarga input de storage, compone
con Pillow (image_compositor), sube el output, y mantiene
RenderJob/MediaAsset consistentes.

Idempotencia (invariante crítico, spec 27): antes de lanzar un render se
comprueba si ya existe un RenderJob SUCCEEDED para el mismo
(content_item_id, template_id, template_version). Si existe, no se vuelve
a componer ni se duplica el MediaAsset de salida — se reutiliza.

El texto de cada zona (hook/cta/título...) viene de la AIGeneration más
reciente asociada al content_item; si no existe ninguna, las zonas quedan
vacías y el compositor simplemente no las dibuja (no se bloquea el render
por falta de guion, pero tampoco se inventa texto aquí)."""
import tempfile
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.media import image_compositor
from app.models.ai_generation import AIGeneration
from app.models.content_item import ContentItem, ContentStatus
from app.models.media_asset import MediaAsset
from app.models.render_job import RenderJob, RenderJobStatus
from app.models.template import Template
from app.storage import s3_client


class RenderError(Exception):
    pass


def find_existing_succeeded_job(
    db: Session, *, content_item_id, template_id, template_version: int, slide_index: int = 0
) -> RenderJob | None:
    return db.scalar(
        select(RenderJob).where(
            RenderJob.content_item_id == content_item_id,
            RenderJob.template_id == template_id,
            RenderJob.template_version == template_version,
            RenderJob.slide_index == slide_index,
            RenderJob.status == RenderJobStatus.SUCCEEDED,
        )
    )


def enqueue_render(
    db: Session, *, content_item_id, template_id, input_asset_id, slide_index: int = 0, worker_id: str | None = None
) -> RenderJob:
    """Crea (o reutiliza) el RenderJob. Nunca lanza un segundo render si ya
    hay uno SUCCEEDED para la misma combinación content+template+version+slide."""
    template = db.get(Template, template_id)
    if not template:
        raise RenderError("Template no encontrado")

    content_item = db.get(ContentItem, content_item_id)
    if not content_item:
        raise RenderError("Content item no encontrado")

    input_asset = db.get(MediaAsset, input_asset_id)
    if not input_asset or input_asset.content_item_id != content_item_id:
        raise RenderError("El asset de entrada no pertenece a este content item")

    existing = find_existing_succeeded_job(
        db,
        content_item_id=content_item_id,
        template_id=template_id,
        template_version=template.version,
        slide_index=slide_index,
    )
    if existing:
        return existing

    current_status = ContentStatus(content_item.status)
    if current_status == ContentStatus.IMPORTED:
        content_item.transition_to(ContentStatus.PROCESSING)
    elif current_status != ContentStatus.PROCESSING:
        raise RenderError(
            f"Solo se puede renderizar contenido IMPORTED o PROCESSING (actual: {current_status})"
        )

    job = RenderJob(
        content_item_id=content_item_id,
        template_id=template_id,
        template_version=template.version,
        slide_index=slide_index,
        input_asset_id=input_asset_id,
        status=RenderJobStatus.QUEUED,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _latest_zone_texts(db: Session, content_item_id) -> dict[str, str | list[str]]:
    generation = db.scalar(
        select(AIGeneration)
        .where(AIGeneration.source_content_id == content_item_id)
        .order_by(AIGeneration.created_at.desc())
    )
    if not generation:
        return {}

    output = generation.output_json
    zone_texts: dict[str, str | list[str]] = dict(output.get("sections", {}))
    zone_texts.setdefault("hook", output.get("hook", ""))
    zone_texts.setdefault("cta", output.get("cta", ""))
    zone_texts.setdefault("title", output.get("title", ""))
    return zone_texts


def run_render_job(db: Session, job_id, *, worker_id: str) -> RenderJob:
    """Ejecuta el render real. Se asume llamado desde el worker de Celery
    (render_worker.py), nunca directamente desde un router HTTP."""
    job = db.get(RenderJob, job_id)
    if not job:
        raise RenderError("RenderJob no encontrado")

    if job.status == RenderJobStatus.SUCCEEDED:
        return job  # idempotente: reintento tardío no debe re-ejecutar

    template = db.get(Template, job.template_id)
    input_asset = db.get(MediaAsset, job.input_asset_id)
    zone_texts = _latest_zone_texts(db, job.content_item_id)

    job.status = RenderJobStatus.RUNNING
    job.worker_id = worker_id
    db.commit()

    try:
        with tempfile.TemporaryDirectory() as tmp:
            local_input = str(Path(tmp) / "input.jpg")
            local_output_ext = template.configuration_json.get("output", {}).get("format", "jpg")
            local_output = str(Path(tmp) / f"output.{local_output_ext}")

            s3_client._client.download_file(s3_client.BUCKET, input_asset.storage_key, local_input)

            logo_path = None
            branding = template.configuration_json.get("branding", {})
            if branding.get("enabled") and branding.get("logo_asset_key"):
                logo_path = str(Path(tmp) / "logo.png")
                s3_client._client.download_file(s3_client.BUCKET, branding["logo_asset_key"], logo_path)

            image_compositor.compose(
                input_path=local_input,
                output_path=local_output,
                config=template.configuration_json,
                zone_texts=zone_texts,
                logo_path=logo_path,
            )

            info = image_compositor.probe(local_output)

            output_key = s3_client.build_storage_key(
                folder="rendered",
                content_item_id=str(job.content_item_id),
                filename=f"{job.id}_slide{job.slide_index}.{local_output_ext}",
            )
            s3_client.upload_file(local_output, output_key)

            output_asset = MediaAsset(
                content_item_id=job.content_item_id,
                storage_key=output_key,
                asset_type="rendered_photo",
                mime_type=f"image/{'jpeg' if local_output_ext == 'jpg' else local_output_ext}",
                width=info.width,
                height=info.height,
            )
            db.add(output_asset)
            db.flush()

            job.output_asset_id = output_asset.id
            job.status = RenderJobStatus.SUCCEEDED
            job.progress = 100
            db.commit()

            content_item = db.get(ContentItem, job.content_item_id)
            statuses = list(
                db.scalars(
                    select(RenderJob.status).where(RenderJob.content_item_id == job.content_item_id)
                )
            )
            all_render_jobs_succeeded = statuses and all(
                RenderJobStatus(status) == RenderJobStatus.SUCCEEDED for status in statuses
            )
            if (
                content_item
                and ContentStatus(content_item.status) == ContentStatus.PROCESSING
                and all_render_jobs_succeeded
            ):
                content_item.transition_to(ContentStatus.READY_FOR_REVIEW)
                db.commit()

    except Exception as exc:  # noqa: BLE001 — se registra el error estructurado, no se oculta
        db.rollback()
        job.status = RenderJobStatus.FAILED
        job.error_code = type(exc).__name__
        job.error_message = str(exc)[:2000]
        db.commit()
        raise

    return job
