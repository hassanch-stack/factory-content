"""Tests del servicio de Review — spec sección 11 + invariante crítico 27:
contenido sin rights_status aceptable no puede entrar a publicación
automática, y eso se bloquea ya en approve(), no solo al programar."""
from unittest.mock import MagicMock

import pytest

from app.models.content_item import ContentStatus
from app.services import review_service


def _make_item(status=ContentStatus.READY_FOR_REVIEW, rights_status="LICENSED"):
    item = MagicMock()
    item.status = status
    item.rights_status = rights_status
    item.can_enter_automatic_publishing.return_value = rights_status in {
        "AUTHORIZED", "LICENSED", "PUBLIC_DOMAIN", "PLATFORM_SUPPORTED",
    }

    def transition_to(new_status):
        item.status = new_status
    item.transition_to.side_effect = transition_to
    return item


def test_approve_blocked_when_rights_not_acceptable():
    db = MagicMock()
    item = _make_item(rights_status="UNKNOWN")
    db.get.return_value = item

    with pytest.raises(review_service.RightsNotAcceptableError):
        review_service.approve(db, "content-1")

    item.transition_to.assert_not_called()
    db.commit.assert_not_called()


def test_approve_succeeds_when_rights_acceptable():
    db = MagicMock()
    item = _make_item(rights_status="LICENSED")
    db.get.return_value = item

    review_service.approve(db, "content-1")

    item.transition_to.assert_called_once_with(ContentStatus.APPROVED)
    db.commit.assert_called_once()
    # Se registra el audit log (db.add se llama para el AuditLog)
    assert db.add.called


def test_bulk_apply_reports_partial_failures_without_stopping():
    db = MagicMock()
    good_item = _make_item(rights_status="LICENSED")
    bad_item = _make_item(rights_status="UNKNOWN")

    def get_side_effect(model, cid):
        return good_item if cid == "good" else bad_item

    db.get.side_effect = get_side_effect

    result = review_service.bulk_apply(db, ["good", "bad"], "approve")

    assert result["succeeded"] == ["good"]
    assert len(result["failed"]) == 1
    assert result["failed"][0]["content_item_id"] == "bad"


def test_bulk_apply_unknown_action_raises():
    db = MagicMock()
    with pytest.raises(review_service.ReviewError):
        review_service.bulk_apply(db, ["x"], "not_a_real_action")
