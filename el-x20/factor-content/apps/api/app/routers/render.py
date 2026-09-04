from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.template import RenderJobCreate, RenderJobOut
from app.services import render_service

router = APIRouter(prefix="/api/render", tags=["render"])


@router.post("/bulk", response_model=list[RenderJobOut], status_code=202)
def bulk_render(payloads: list[RenderJobCreate], db: Session = Depends(get_db)):
    """Encola N renders. No compone la foto en el request — solo crea/reutiliza
    los RenderJob y deja que render_worker los procese (spec 9/22)."""
    jobs = []
    for payload in payloads:
        try:
            job = render_service.enqueue_render(
                db,
                content_item_id=payload.content_item_id,
                template_id=payload.template_id,
                input_asset_id=payload.input_asset_id,
                slide_index=payload.slide_index,
            )
        except render_service.RenderError as exc:
            raise HTTPException(400, str(exc)) from exc
        jobs.append(job)

    # Crear primero todos los jobs del carrusel. Si se lanzara el worker
    # dentro del bucle, la primera diapositiva podría terminar antes de que
    # existan las demás y el contenido entraría prematuramente en revisión.
    from workers.render_worker import execute_render_job
    for job in jobs:
        if job.status == "QUEUED":
            execute_render_job.delay(str(job.id))

    return jobs


@router.get("/jobs/{job_id}", response_model=RenderJobOut)
def get_render_job(job_id, db: Session = Depends(get_db)):
    from app.models.render_job import RenderJob
    job = db.get(RenderJob, job_id)
    if not job:
        raise HTTPException(404, "RenderJob no encontrado")
    return job
