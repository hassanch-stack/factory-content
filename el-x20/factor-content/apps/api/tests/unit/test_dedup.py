"""Tests de deduplicación — spec 5.2: external_id > URL canónica > checksum."""
from unittest.mock import MagicMock

from app.services.dedup_service import find_duplicate


def test_finds_duplicate_by_external_id():
    db = MagicMock()
    fake_existing = MagicMock()
    db.scalar.return_value = fake_existing

    result = find_duplicate(
        db, source_id="src-1", external_id="ext-123", source_url="https://x.com/a"
    )
    assert result is fake_existing
    db.scalar.assert_called_once()


def test_no_duplicate_returns_none():
    db = MagicMock()
    db.scalar.return_value = None

    result = find_duplicate(
        db, source_id="src-1", external_id="ext-999", source_url="https://x.com/new"
    )
    assert result is None
    # Debe intentar las 3 estrategias antes de rendirse (external_id, URL, checksum=None -> se salta)
    assert db.scalar.call_count == 2
