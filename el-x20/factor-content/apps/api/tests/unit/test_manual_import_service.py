from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock
import uuid

import pytest
from PIL import Image

from app.models.content_item import ContentStatus
from app.services import manual_import_service


def _jpeg_bytes() -> BytesIO:
    buffer = BytesIO()
    Image.new("RGB", (12, 8), color="navy").save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer


def test_manual_import_creates_imported_content_and_original_asset(monkeypatch):
    db = MagicMock()
    db.scalar.return_value = None
    source = SimpleNamespace(id=uuid.uuid4())
    monkeypatch.setattr(manual_import_service, "_get_or_create_manual_source", lambda _: source)
    upload_file = MagicMock()
    monkeypatch.setattr(manual_import_service.s3_client, "upload_file", upload_file)

    imported = manual_import_service.import_manual_image(
        db,
        file=_jpeg_bytes(),
        filename="noticia.jpg",
        title="Titular",
        description=None,
        category=None,
        language="es",
        rights_status="authorized",
        max_upload_size_bytes=1024 * 1024,
    )

    assert imported.content_item.status == ContentStatus.IMPORTED
    assert imported.content_item.rights_status == "AUTHORIZED"
    assert imported.content_item.metadata_json["origin"] == "manual_upload"
    assert imported.media_asset.mime_type == "image/jpeg"
    assert (imported.media_asset.width, imported.media_asset.height) == (12, 8)
    upload_file.assert_called_once()
    db.commit.assert_called_once()


def test_manual_import_rejects_non_image_before_storage(monkeypatch):
    upload_file = MagicMock()
    monkeypatch.setattr(manual_import_service.s3_client, "upload_file", upload_file)

    with pytest.raises(manual_import_service.ManualImportError, match="imagen válida"):
        manual_import_service.import_manual_image(
            MagicMock(),
            file=BytesIO(b"not an image"),
            filename="imagen.jpg",
            title=None,
            description=None,
            category=None,
            language=None,
            rights_status="UNKNOWN",
            max_upload_size_bytes=1024 * 1024,
        )

    upload_file.assert_not_called()


def test_manual_import_rejects_oversized_file():
    with pytest.raises(manual_import_service.ManualImportError, match="supera el límite"):
        manual_import_service.import_manual_image(
            MagicMock(),
            file=BytesIO(b"x" * 21),
            filename="imagen.jpg",
            title=None,
            description=None,
            category=None,
            language=None,
            rights_status="UNKNOWN",
            max_upload_size_bytes=20,
        )
