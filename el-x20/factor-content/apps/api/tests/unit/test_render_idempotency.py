"""Invariante crítico (spec 27): un reintento nunca duplica el output de un
render ya SUCCEEDED. Se testea contra find_existing_succeeded_job, que es
la guardia que usa enqueue_render antes de crear un nuevo RenderJob."""
from unittest.mock import MagicMock

from app.services.render_service import find_existing_succeeded_job


def test_returns_existing_succeeded_job_without_creating_new_one():
    db = MagicMock()
    existing_job = MagicMock()
    db.scalar.return_value = existing_job

    result = find_existing_succeeded_job(
        db, content_item_id="c1", template_id="t1", template_version=1
    )

    assert result is existing_job
    db.scalar.assert_called_once()


def test_no_existing_job_returns_none():
    db = MagicMock()
    db.scalar.return_value = None

    result = find_existing_succeeded_job(
        db, content_item_id="c1", template_id="t1", template_version=1
    )
    assert result is None
