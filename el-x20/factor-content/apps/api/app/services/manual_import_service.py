"""Importación manual de fotos aportadas por el operador.

No consulta ni descarga fuentes externas: el contenido entra al sistema solo
cuando el operador selecciona y sube un archivo desde la interfaz.
"""
from __future__ import annotations

import hashlib
import os
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content_item import ContentItem, ContentStatus
from app.models.media_asset import MediaAsset
from app.models.source import PermissionStatus, Source
from app.storage import s3_client

MANUAL_SOURCE_URL = "manual://operator-upload"
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_RIGHTS_STATUSES = {
    "UNKNOWN",
    "AUTHORIZED",
    "LICENSED",
    "PUBLIC_DOMAIN",
    "PLATFORM_SUPPORTED",
    "RESTRICTED",
    "REJECTED",
}


class ManualImportError(Exception):
    """Error seguro para mostrar al operador durante una carga manual."""


class DuplicateManualImportError(ManualImportError):
    def __init__(self, content_item: ContentItem) -> None:
        self.content_item = content_item
        super().__init__("Esta foto ya está en la cola de contenido.")


@dataclass(frozen=True)
class ImportedManualContent:
    content_item: ContentItem
    media_asset: MediaAsset


def import_manual_image(
    db: Session,
    *,
    file: BinaryIO,
    filename: str | None,
    title: str | None,
    description: str | None,
    category: str | None,
    language: str | None,
    rights_status: str,
    max_upload_size_bytes: int,
) -> ImportedManualContent:
    """Valida, deduplica y almacena una foto subida manualmente.

    La verificación usa Pillow sobre el binario, no la extensión ni el MIME
    declarado por el navegador. El objeto se elimina del storage si la
    transacción de base de datos no termina correctamente.
    """
    normalized_rights_status = rights_status.upper().strip()
    if normalized_rights_status not in ALLOWED_RIGHTS_STATUSES:
        raise ManualImportError("El estado de derechos indicado no es válido.")

    temp_path, file_size, checksum = _write_temp_file(
        file, filename=filename, max_upload_size_bytes=max_upload_size_bytes
    )
    uploaded_key: str | None = None
    committed = False
    try:
        mime_type, width, height = _inspect_image(temp_path)

        duplicate = db.scalar(select(ContentItem).where(ContentItem.checksum == checksum))
        if duplicate:
            raise DuplicateManualImportError(duplicate)

        source = _get_or_create_manual_source(db)
        content_item = ContentItem(
            id=uuid.uuid4(),
            source_id=source.id,
            source_url="",
            title=title or None,
            description=description or None,
            category=category or None,
            language=language or None,
            rights_status=normalized_rights_status,
            checksum=checksum,
            status=ContentStatus.IMPORTING,
            metadata_json={"origin": "manual_upload", "original_filename": _safe_filename(filename)},
        )
        content_item.source_url = f"manual://uploads/{content_item.id}"
        db.add(content_item)
        db.flush()

        uploaded_key = s3_client.build_storage_key(
            folder="originals", content_item_id=str(content_item.id), filename=_safe_filename(filename)
        )
        s3_client.upload_file(temp_path, uploaded_key)

        media_asset = MediaAsset(
            content_item_id=content_item.id,
            storage_key=uploaded_key,
            asset_type="original",
            mime_type=mime_type,
            width=width,
            height=height,
            file_size=file_size,
            checksum=checksum,
        )
        content_item.transition_to(ContentStatus.IMPORTED)
        db.add(media_asset)
        db.commit()
        committed = True
        db.refresh(content_item)
        db.refresh(media_asset)
        return ImportedManualContent(content_item=content_item, media_asset=media_asset)
    except Exception:
        db.rollback()
        if uploaded_key and not committed:
            try:
                s3_client.delete_object(uploaded_key)
            except Exception:
                pass
        raise
    finally:
        os.unlink(temp_path)


def _get_or_create_manual_source(db: Session) -> Source:
    source = db.scalar(
        select(Source).where(Source.platform == "MANUAL", Source.source_url == MANUAL_SOURCE_URL)
    )
    if source:
        return source

    source = Source(
        name="Cargas manuales del operador",
        platform="MANUAL",
        source_url=MANUAL_SOURCE_URL,
        permission_status=PermissionStatus.AUTHORIZED,
        active=True,
        polling_interval=0,
    )
    db.add(source)
    db.flush()
    return source


def _write_temp_file(
    file: BinaryIO, *, filename: str | None, max_upload_size_bytes: int
) -> tuple[str, int, str]:
    suffix = Path(_safe_filename(filename)).suffix
    digest = hashlib.sha256()
    file_size = 0
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_path = temp_file.name
        while chunk := file.read(1024 * 1024):
            file_size += len(chunk)
            if file_size > max_upload_size_bytes:
                temp_file.close()
                os.unlink(temp_path)
                raise ManualImportError(
                    f"El archivo supera el límite de {max_upload_size_bytes // (1024 * 1024)} MB."
                )
            digest.update(chunk)
            temp_file.write(chunk)

    if file_size == 0:
        os.unlink(temp_path)
        raise ManualImportError("Selecciona una imagen que no esté vacía.")
    return temp_path, file_size, digest.hexdigest()


def _inspect_image(temp_path: str) -> tuple[str, int, int]:
    try:
        with Image.open(temp_path) as image:
            image.verify()
        with Image.open(temp_path) as image:
            mime_type = Image.MIME.get(image.format)
            if mime_type not in ALLOWED_IMAGE_MIME_TYPES:
                raise ManualImportError("Solo se admiten fotos JPEG, PNG o WebP.")
            return mime_type, image.width, image.height
    except (UnidentifiedImageError, OSError) as exc:
        raise ManualImportError("El archivo no es una imagen válida.") from exc


def _safe_filename(filename: str | None) -> str:
    candidate = (filename or "foto").replace("/", "_").replace("\\", "_").replace("..", "_")
    return candidate or "foto"
