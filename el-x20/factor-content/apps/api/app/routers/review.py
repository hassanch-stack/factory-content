import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.ai_generation import AIGeneration
from app.models.content_item import ContentItem
from app.models.media_asset import MediaAsset
from app.schemas.review import (
    BulkActionPayload,
    BulkActionResult,
    CopyrightReviewPayload,
    MetadataEditPayload,
    RejectPayload,
    ReviewItemOut,
    ReviewMediaOut,
)
from app.services import review_service
from app.storage import s3_client

router = APIRouter(prefix="/api/review", tags=["review"])


def _to_review_item(db: Session, item: ContentItem) -> ReviewItemOut:
    generation = db.scalar(
        select(AIGeneration)
        .where(AIGeneration.source_content_id == item.id)
        .order_by(AIGeneration.created_at.desc())
    )
    rendered = db.scalar(
        select(MediaAsset)
        .where(MediaAsset.content_item_id == item.id, MediaAsset.asset_type == "rendered_photo")
        .order_by(MediaAsset.created_at.desc())
    )
    preview = None
    if rendered:
        preview = ReviewMediaOut(
            media_asset_id=rendered.id,
            preview_url=s3_client.generate_presigned_url(rendered.storage_key),
            asset_type=rendered.asset_type,
        )

    return ReviewItemOut(
        content_item_id=item.id,
        title=item.title,
        status=item.status,
        rights_status=item.rights_status,
        factor_score=item.factor_score,
        ai_output=generation.output_json if generation else None,
        preview=preview,
    )


@router.get("", response_model=list[ReviewItemOut])
def list_review_queue(db: Session = Depends(get_db)) -> list[ReviewItemOut]:
    """Cola de revisión — por defecto, todo lo READY_FOR_REVIEW (spec 11).
    Usa siempre la foto ya renderizada + el guion generado, nunca el
    original crudo, para que el operador revise exactamente lo que se
    publicaría."""
    items = db.scalars(select(ContentItem).where(ContentItem.status == "READY_FOR_REVIEW"))
    return [_to_review_item(db, item) for item in items]


@router.get("/{content_item_id}", response_model=ReviewItemOut)
def get_review_item(content_item_id: uuid.UUID, db: Session = Depends(get_db)) -> ReviewItemOut:
    item = db.get(ContentItem, content_item_id)
    if not item:
        raise HTTPException(404, "Content item no encontrado")
    return _to_review_item(db, item)


@router.post("/{content_item_id}/approve", response_model=ReviewItemOut)
def approve(content_item_id: uuid.UUID, db: Session = Depends(get_db)) -> ReviewItemOut:
    try:
        item = review_service.approve(db, content_item_id)
    except review_service.RightsNotAcceptableError as exc:
        raise HTTPException(422, str(exc)) from exc
    except review_service.ReviewError as exc:
        raise HTTPException(409, str(exc)) from exc
    return _to_review_item(db, item)


@router.post("/{content_item_id}/reject", response_model=ReviewItemOut)
def reject(content_item_id: uuid.UUID, payload: RejectPayload, db: Session = Depends(get_db)) -> ReviewItemOut:
    try:
        item = review_service.reject(db, content_item_id, reason=payload.reason)
    except review_service.ReviewError as exc:
        raise HTTPException(409, str(exc)) from exc
    return _to_review_item(db, item)


@router.post("/{content_item_id}/copyright-review", response_model=ReviewItemOut)
def mark_copyright_review(
    content_item_id: uuid.UUID, payload: CopyrightReviewPayload, db: Session = Depends(get_db)
) -> ReviewItemOut:
    try:
        item = review_service.mark_copyright_review(db, content_item_id, reason=payload.reason)
    except review_service.ReviewError as exc:
        raise HTTPException(409, str(exc)) from exc
    return _to_review_item(db, item)


@router.post("/{content_item_id}/send-back", response_model=ReviewItemOut)
def send_back(content_item_id: uuid.UUID, db: Session = Depends(get_db)) -> ReviewItemOut:
    try:
        item = review_service.send_back_to_processing(db, content_item_id)
    except review_service.ReviewError as exc:
        raise HTTPException(409, str(exc)) from exc
    return _to_review_item(db, item)


@router.patch("/{content_item_id}/metadata", response_model=ReviewItemOut)
def edit_metadata(
    content_item_id: uuid.UUID, payload: MetadataEditPayload, db: Session = Depends(get_db)
) -> ReviewItemOut:
    """Edita el output de la última AIGeneration del item — nunca crea una
    generación nueva, edita la existente y la marca edited_by_user=True
    (spec 10: 'AI output must be editable by the user')."""
    item = db.get(ContentItem, content_item_id)
    if not item:
        raise HTTPException(404, "Content item no encontrado")

    generation = db.scalar(
        select(AIGeneration)
        .where(AIGeneration.source_content_id == content_item_id)
        .order_by(AIGeneration.created_at.desc())
    )
    if not generation:
        raise HTTPException(404, "No hay generación de IA para este content item")

    updated = dict(generation.output_json)
    for field in ("title", "cta", "hook", "hashtags", "keywords"):
        value = getattr(payload, field)
        if value is not None:
            updated[field] = value
    if payload.sections is not None:
        updated["sections"] = {**updated.get("sections", {}), **payload.sections}

    generation.output_json = updated
    generation.edited_by_user = True
    db.commit()

    return _to_review_item(db, item)


@router.post("/bulk", response_model=BulkActionResult)
def bulk_action(payload: BulkActionPayload, db: Session = Depends(get_db)) -> BulkActionResult:
    if payload.action not in {"approve", "reject", "mark_copyright_review"}:
        raise HTTPException(422, f"Acción bulk no soportada: {payload.action}")
    result = review_service.bulk_apply(
        db, payload.content_item_ids, payload.action, reason=payload.reason
    )
    return BulkActionResult(**result)
