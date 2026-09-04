import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.script_template import ScriptTemplate
from app.schemas.script_template import ScriptTemplateCreate, ScriptTemplateOut
from app.schemas.script_template_config import ScriptTemplateConfiguration

router = APIRouter(prefix="/api/script-templates", tags=["script-templates"])


def _validate(raw_config: dict) -> ScriptTemplateConfiguration:
    try:
        return ScriptTemplateConfiguration.model_validate(raw_config)
    except ValidationError as exc:
        raise HTTPException(422, f"Configuración de script template inválida: {exc}") from exc


@router.get("", response_model=list[ScriptTemplateOut])
def list_script_templates(db: Session = Depends(get_db)) -> list[ScriptTemplate]:
    return list(db.scalars(select(ScriptTemplate).where(ScriptTemplate.active.is_(True))))


@router.post("", response_model=ScriptTemplateOut, status_code=201)
def create_script_template(payload: ScriptTemplateCreate, db: Session = Depends(get_db)) -> ScriptTemplate:
    validated = _validate(payload.configuration_json)
    template = ScriptTemplate(name=payload.name, version=1, configuration_json=validated.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.post("/{template_id}/new-version", response_model=ScriptTemplateOut, status_code=201)
def new_version(template_id: uuid.UUID, payload: ScriptTemplateCreate, db: Session = Depends(get_db)) -> ScriptTemplate:
    current = db.get(ScriptTemplate, template_id)
    if not current:
        raise HTTPException(404, "Script template no encontrado")
    validated = _validate(payload.configuration_json)
    new_tpl = ScriptTemplate(
        name=payload.name or current.name,
        version=current.version + 1,
        configuration_json=validated.model_dump(),
    )
    current.active = False
    db.add(new_tpl)
    db.commit()
    db.refresh(new_tpl)
    return new_tpl
