"""Lógica de Review — spec sección 11. Ningún router llama a
item.transition_to(...) directamente para acciones de revisión: todo pasa
por aquí, para que el gate de rights_status y el audit log sean
imposibles de saltarse."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_generation import AIGeneration
from app.models.content_item import ContentItem, ContentStatus, InvalidTransitionError
from app.services import audit_service


class ReviewError(Exception):
    pass


class RightsNotAcceptableError(ReviewError):
    """Invariante crítico (spec 27): contenido sin rights_status aceptable
    no puede entrar a publicación automática. Se aplica ya en la
    aprobación, no solo al programar, para no dejar pasar el problema más
    adelante en el pipeline."""


def get_review_item(db: Session, content_item_id) -> tuple[ContentItem, dict | None]:
    item = db.get(ContentItem, content_item_id)
    if not item:
        raise ReviewError("Content item no encontrado")
    generation = db.scalar(
        select(AIGeneration)
        .where(AIGeneration.source_content_id == content_item_id)
        .order_by(AIGeneration.created_at.desc())
    )
    return item, (generation.output_json if generation else None)


def approve(db: Session, content_item_id, *, user_id=None) -> ContentItem:
    item = db.get(ContentItem, content_item_id)
    if not item:
        raise ReviewError("Content item no encontrado")

    if not item.can_enter_automatic_publishing():
        raise RightsNotAcceptableError(
            f"rights_status='{item.rights_status}' no es aceptable para aprobar/publicar"
        )

    before = {"status": item.status.value}
    try:
        item.transition_to(ContentStatus.APPROVED)
    except InvalidTransitionError as exc:
        raise ReviewError(str(exc)) from exc

    audit_service.record(
        db, user_id=user_id, action="content.approve", entity_type="content_item",
        entity_id=item.id, before=before, after={"status": item.status.value},
    )
    db.commit()
    db.refresh(item)
    return item


def reject(db: Session, content_item_id, *, reason: str | None = None, user_id=None) -> ContentItem:
    item = db.get(ContentItem, content_item_id)
    if not item:
        raise ReviewError("Content item no encontrado")

    before = {"status": item.status.value}
    try:
        item.transition_to(ContentStatus.REJECTED)
    except InvalidTransitionError as exc:
        raise ReviewError(str(exc)) from exc

    audit_service.record(
        db, user_id=user_id, action="content.reject", entity_type="content_item",
        entity_id=item.id, before=before,
        after={"status": item.status.value, "reason": reason},
    )
    db.commit()
    db.refresh(item)
    return item


def mark_copyright_review(db: Session, content_item_id, *, reason: str | None = None, user_id=None) -> ContentItem:
    item = db.get(ContentItem, content_item_id)
    if not item:
        raise ReviewError("Content item no encontrado")

    before = {"status": item.status.value}
    try:
        item.transition_to(ContentStatus.COPYRIGHT_REVIEW)
    except InvalidTransitionError as exc:
        raise ReviewError(str(exc)) from exc

    audit_service.record(
        db, user_id=user_id, action="content.mark_copyright_review", entity_type="content_item",
        entity_id=item.id, before=before,
        after={"status": item.status.value, "reason": reason},
    )
    db.commit()
    db.refresh(item)
    return item


def send_back_to_processing(db: Session, content_item_id, *, user_id=None) -> ContentItem:
    """'send back to processing' del spec 11 — por ejemplo, para forzar un
    nuevo render con otra plantilla tras revisar el resultado."""
    item = db.get(ContentItem, content_item_id)
    if not item:
        raise ReviewError("Content item no encontrado")

    before = {"status": item.status.value}
    try:
        item.transition_to(ContentStatus.PROCESSING)
    except InvalidTransitionError as exc:
        raise ReviewError(str(exc)) from exc

    audit_service.record(
        db, user_id=user_id, action="content.send_back_to_processing", entity_type="content_item",
        entity_id=item.id, before=before, after={"status": item.status.value},
    )
    db.commit()
    db.refresh(item)
    return item


def bulk_apply(db: Session, content_item_ids: list, action: str, *, reason: str | None = None, user_id=None):
    """Acciones bulk (spec 11): approve/reject/mark_copyright_review sobre
    varios items. Cada item se procesa de forma independiente — un fallo
    en uno no revierte los demás, pero se reporta cuál falló y por qué."""
    handlers = {
        "approve": lambda db, cid: approve(db, cid, user_id=user_id),
        "reject": lambda db, cid: reject(db, cid, reason=reason, user_id=user_id),
        "mark_copyright_review": lambda db, cid: mark_copyright_review(db, cid, reason=reason, user_id=user_id),
    }
    handler = handlers.get(action)
    if not handler:
        raise ReviewError(f"Acción bulk desconocida: {action}")

    results = {"succeeded": [], "failed": []}
    for cid in content_item_ids:
        try:
            handler(db, cid)
            results["succeeded"].append(str(cid))
        except ReviewError as exc:
            results["failed"].append({"content_item_id": str(cid), "error": str(exc)})
    return results
