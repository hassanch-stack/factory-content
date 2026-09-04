"""Factor Score debe ser determinista: mismo input -> mismo output siempre
(spec 6, definición de done de Phase 6)."""
from datetime import datetime, timedelta, timezone

from app.services.scoring_service import compute_factor_score


def test_deterministic_for_same_input():
    now = datetime.now(timezone.utc)
    published_at = now - timedelta(hours=2)

    result_a = compute_factor_score(published_at=published_at, source_priority=8, now=now)
    result_b = compute_factor_score(published_at=published_at, source_priority=8, now=now)

    assert result_a.total == result_b.total
    assert result_a.components == result_b.components


def test_score_in_valid_range():
    result = compute_factor_score(published_at=datetime.now(timezone.utc), source_priority=10)
    assert 0 <= result.total <= 100


def test_more_recent_scores_higher_recency_component():
    now = datetime.now(timezone.utc)
    fresh = compute_factor_score(published_at=now, source_priority=5)
    old = compute_factor_score(published_at=now - timedelta(hours=40), source_priority=5)
    assert fresh.components["recency"] > old.components["recency"]


def test_missing_data_defaults_to_neutral_not_error():
    result = compute_factor_score(published_at=None, source_priority=0)
    assert 0 <= result.total <= 100  # no lanza excepción por falta de histórico
