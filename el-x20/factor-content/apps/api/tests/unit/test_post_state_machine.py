"""Máquina de estados de Post (spec 15) — PUBLISHED es terminal, nunca se
revierte un post ya publicado."""
import pytest

from app.models.post import InvalidPostTransitionError, Post, PostStatus


def _post(status: PostStatus) -> Post:
    p = Post()
    p.status = status
    return p


def test_published_is_terminal():
    p = _post(PostStatus.PUBLISHED)
    with pytest.raises(InvalidPostTransitionError):
        p.transition_to(PostStatus.SCHEDULED)


def test_failed_can_retry_to_scheduled():
    p = _post(PostStatus.FAILED)
    p.transition_to(PostStatus.SCHEDULED)
    assert p.status == PostStatus.SCHEDULED


def test_publishing_cannot_go_directly_to_scheduled():
    p = _post(PostStatus.PUBLISHING)
    with pytest.raises(InvalidPostTransitionError):
        p.transition_to(PostStatus.SCHEDULED)
