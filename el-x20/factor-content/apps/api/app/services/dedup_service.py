"""Deduplicación de ContentItem — spec sección 5.2.

Orden de verificación (el más fuerte primero):
1. external_id dentro de la misma source
2. URL canónica de la fuente
3. checksum del media (si ya se importó)
Perceptual hash queda fuera de V1 (mencionado como "where useful" en el
spec, no obligatorio).
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content_item import ContentItem


def find_duplicate(
    db: Session,
    *,
    source_id,
    external_id: str | None,
    source_url: str,
    checksum: str | None = None,
) -> ContentItem | None:
    if external_id:
        existing = db.scalar(
            select(ContentItem).where(
                ContentItem.source_id == source_id,
                ContentItem.external_id == external_id,
            )
        )
        if existing:
            return existing

    existing = db.scalar(select(ContentItem).where(ContentItem.source_url == source_url))
    if existing:
        return existing

    if checksum:
        existing = db.scalar(select(ContentItem).where(ContentItem.checksum == checksum))
        if existing:
            return existing

    return None
