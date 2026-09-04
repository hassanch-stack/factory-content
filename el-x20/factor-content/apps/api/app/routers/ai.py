from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.ai_generation import AIGeneration
from app.models.content_item import ContentItem
from app.models.script_template import ScriptTemplate
from app.schemas.ai_generation import AIGenerationCreate, AIGenerationEdit, AIGenerationOut
from app.services.ai_service import PROMPT_VERSION, MODEL_NAME, AIGenerationError, rewrite_script

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/rewrite-script", response_model=AIGenerationOut, status_code=201)
def rewrite_existing_script(payload: AIGenerationCreate, db: Session = Depends(get_db)) -> AIGeneration:
    content_item = db.get(ContentItem, payload.content_item_id)
    if not content_item:
        raise HTTPException(404, "Content item no encontrado")

    script_template = db.get(ScriptTemplate, payload.script_template_id)
    if not script_template:
        raise HTTPException(404, "Script template no encontrado")

    try:
        result = rewrite_script(content_item, script_template.configuration_json)
    except AIGenerationError as exc:
        raise HTTPException(422, str(exc)) from exc

    generation = AIGeneration(
        source_content_id=content_item.id,
        script_template_id=script_template.id,
        model=MODEL_NAME,
        prompt_version=PROMPT_VERSION,
        output_json=result.model_dump(),
        edited_by_user=False,
    )
    db.add(generation)
    db.commit()
    db.refresh(generation)
    return generation


@router.patch("/generations/{generation_id}", response_model=AIGenerationOut)
def edit_generation(generation_id, payload: AIGenerationEdit, db: Session = Depends(get_db)) -> AIGeneration:
    """El operador siempre puede editar el output de la IA (spec 10:
    'AI output must be editable by the user'). Marcar edited_by_user=True
    deja rastro de que ya no es el texto crudo generado."""
    generation = db.get(AIGeneration, generation_id)
    if not generation:
        raise HTTPException(404, "Generación no encontrada")
    generation.output_json = payload.output_json
    generation.edited_by_user = True
    db.commit()
    db.refresh(generation)
    return generation
