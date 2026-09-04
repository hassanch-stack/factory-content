"""Invariante crítico (spec sección 27): contenido aprobado no puede
volverse rechazado por accidente; toda transición pasa por el mapa
explícito de VALID_TRANSITIONS."""
import pytest

from app.models.content_item import ContentItem, ContentStatus, InvalidTransitionError


def _item(status: ContentStatus) -> ContentItem:
    item = ContentItem()
    item.status = status
    return item


def test_valid_transition_discovered_to_selected():
    item = _item(ContentStatus.DISCOVERED)
    item.transition_to(ContentStatus.SELECTED)
    assert item.status == ContentStatus.SELECTED


def test_transition_works_after_status_is_reloaded_as_a_string():
    """Las columnas históricas son VARCHAR; una lectura desde Postgres puede
    devolver el valor como str y no debe inutilizar la máquina de estados."""
    item = _item(ContentStatus.IMPORTED)
    item.status = "IMPORTED"
    item.transition_to(ContentStatus.PROCESSING)
    assert item.status == ContentStatus.PROCESSING


def test_approved_cannot_jump_directly_to_rejected():
    """APPROVED -> REJECTED no está en el mapa de transiciones válidas:
    una vez aprobado, solo se puede archivar o programar."""
    item = _item(ContentStatus.APPROVED)
    with pytest.raises(InvalidTransitionError):
        item.transition_to(ContentStatus.REJECTED)


def test_archived_is_terminal():
    item = _item(ContentStatus.ARCHIVED)
    with pytest.raises(InvalidTransitionError):
        item.transition_to(ContentStatus.SELECTED)


def test_rights_status_gate_for_automatic_publishing():
    item = _item(ContentStatus.APPROVED)
    item.rights_status = "UNKNOWN"
    assert item.can_enter_automatic_publishing() is False

    item.rights_status = "LICENSED"
    assert item.can_enter_automatic_publishing() is True
