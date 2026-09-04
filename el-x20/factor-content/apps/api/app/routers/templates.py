import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.media.template_engine import InvalidTemplateConfigError, validate_configuration
from app.models.template import Template
from app.schemas.template import TemplateCreate, TemplateOut

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("", response_model=list[TemplateOut])
def list_templates(db: Session = Depends(get_db)) -> list[Template]:
    return list(db.scalars(select(Template).where(Template.active.is_(True))))


@router.post("", response_model=TemplateOut, status_code=201)
def create_template(payload: TemplateCreate, db: Session = Depends(get_db)) -> Template:
    try:
        validated = validate_configuration(payload.configuration_json)
    except InvalidTemplateConfigError as exc:
        raise HTTPException(422, f"Configuración de template inválida: {exc}") from exc

    template = Template(
        name=payload.name,
        version=1,
        configuration_json=validated.model_dump(),
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.post("/{template_id}/new-version", response_model=TemplateOut, status_code=201)
def create_new_version(
    template_id: uuid.UUID, payload: TemplateCreate, db: Session = Depends(get_db)
) -> Template:
    """Versionado obligatorio (spec 8): nunca se edita un template en sitio,
    se crea una nueva versión. Renders ya SUCCEEDED conservan qué versión
    exacta usaron (RenderJob.template_version)."""
    current = db.get(Template, template_id)
    if not current:
        raise HTTPException(404, "Template no encontrado")

    try:
        validated = validate_configuration(payload.configuration_json)
    except InvalidTemplateConfigError as exc:
        raise HTTPException(422, f"Configuración de template inválida: {exc}") from exc

    new_version = Template(
        name=payload.name or current.name,
        version=current.version + 1,
        configuration_json=validated.model_dump(),
    )
    current.active = False
    db.add(new_version)
    db.commit()
    db.refresh(new_version)
    return new_version
