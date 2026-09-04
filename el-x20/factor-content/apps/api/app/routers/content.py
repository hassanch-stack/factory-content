import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.models.content_item import ContentItem, InvalidTransitionError
from app.models.media_asset import MediaAsset
from app.schemas.content_item import (
    ContentItemOut,
    ContentItemTransition,
    ManualImportOut,
    MediaAssetOut,
)
from app.services.manual_import_service import (
    DuplicateManualImportError,
    ManualImportError,
    import_manual_image,
)

router = APIRouter(prefix="/api/content", tags=["content"])


@router.post("/import", response_model=ManualImportOut, status_code=201)
def import_content_manually(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    original_script: str = Form(...),
    category: str | None = Form(None),
    language: str | None = Form(None),
    rights_status: str = Form("UNKNOWN"),
    db: Session = Depends(get_db),
) -> ManualImportOut:
    """Crea un elemento de contenido a partir de una foto subida por el operador."""
    try:
        imported = import_manual_image(
            db,
            file=file.file,
            filename=file.filename,
            title=title,
            description=original_script,
            category=category,
            language=language,
            rights_status=rights_status,
            max_upload_size_bytes=get_settings().max_upload_size_bytes,
        )
    except DuplicateManualImportError as exc:
        raise HTTPException(
            status_code=409,
            detail={"message": str(exc), "content_item_id": str(exc.content_item.id)},
        ) from exc
    except ManualImportError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        file.file.close()

    item = imported.content_item
    asset = imported.media_asset
    return ManualImportOut(
        id=item.id,
        source_id=item.source_id,
        title=item.title,
        category=item.category,
        language=item.language,
        factor_score=item.factor_score,
        status=item.status,
        rights_status=item.rights_status,
        created_at=item.created_at,
        updated_at=item.updated_at,
        media_asset_id=asset.id,
        mime_type=asset.mime_type or "",
        width=asset.width or 0,
        height=asset.height or 0,
        file_size=asset.file_size or 0,
    )


@router.get("", response_model=list[ContentItemOut])
def list_content(status: str | None = None, db: Session = Depends(get_db)) -> list[ContentItem]:
    query = select(ContentItem).order_by(ContentItem.factor_score.desc())
    if status:
        query = query.where(ContentItem.status == status)
    return list(db.scalars(query))


@router.get("/{content_id}", response_model=ContentItemOut)
def get_content(content_id: uuid.UUID, db: Session = Depends(get_db)) -> ContentItem:
    item = db.get(ContentItem, content_id)
    if not item:
        raise HTTPException(404, "Content item no encontrado")
    return item


@router.get("/{content_id}/assets", response_model=list[MediaAssetOut])
def list_content_assets(content_id: uuid.UUID, db: Session = Depends(get_db)) -> list[MediaAsset]:
    """Devuelve referencias de media para que el operador pueda iniciar el render.

    Las claves internas de object storage no se exponen: la pantalla de edición
    solo necesita el identificador del asset para crear trabajos de render.
    """
    item = db.get(ContentItem, content_id)
    if not item:
        raise HTTPException(404, "Content item no encontrado")
    return list(
        db.scalars(
            select(MediaAsset)
            .where(MediaAsset.content_item_id == content_id)
            .order_by(MediaAsset.created_at)
        )
    )


@router.post("/{content_id}/select", response_model=ContentItemOut)
def select_content(content_id: uuid.UUID, db: Session = Depends(get_db)) -> ContentItem:
    item = db.get(ContentItem, content_id)
    if not item:
        raise HTTPException(404, "Content item no encontrado")
    try:
        item.transition_to(item.status.__class__.SELECTED)
    except InvalidTransitionError as exc:
        raise HTTPException(409, str(exc)) from exc
    db.commit()
    db.refresh(item)
    return item


@router.post("/{content_id}/transition", response_model=ContentItemOut)
def transition_content(
    content_id: uuid.UUID, payload: ContentItemTransition, db: Session = Depends(get_db)
) -> ContentItem:
    """Endpoint genérico de transición — usado por Review (approve/reject)
    y por los workers internamente vía el mismo servicio."""
    item = db.get(ContentItem, content_id)
    if not item:
        raise HTTPException(404, "Content item no encontrado")
    try:
        item.transition_to(payload.new_status)
    except InvalidTransitionError as exc:
        raise HTTPException(409, str(exc)) from exc
    db.commit()
    db.refresh(item)
    return item
