"""Factor Score — spec sección 17: V1 es rule-based, 0-100, explicable.
NO se construye ML aquí (regla explícita del spec: 'Do not prematurely
build machine learning'). Los pesos son los del spec original y se
guardan en una constante nombrada para poder ajustarlos sin tocar la
lógica de cálculo."""
from dataclasses import dataclass
from datetime import datetime, timezone

WEIGHTS = {
    "recency": 0.20,
    "source_priority": 0.15,
    "topic_potential": 0.20,
    "historical_source_performance": 0.15,
    "category_performance": 0.15,
    "early_engagement": 0.15,
}


@dataclass
class ScoreBreakdown:
    total: int  # 0-100
    components: dict[str, float]  # cada componente ya normalizado 0-100, antes de aplicar el peso
    weighted: dict[str, float]  # componente * peso, lo que realmente suma al total
    explanation: str


def _recency_score(published_at: datetime | None, *, now: datetime | None = None) -> float:
    """Más reciente = score más alto. Decae linealmente a 0 en 48h; nada
    de exponenciales innecesarios (spec: mantenerlo simple en V1)."""
    if not published_at:
        return 0.0
    now = now or datetime.now(timezone.utc)
    hours_old = max((now - published_at).total_seconds() / 3600, 0)
    return max(0.0, 100.0 - (hours_old / 48 * 100))


def _source_priority_score(priority: int) -> float:
    """priority del modelo Source es un entero libre del operador; se
    normaliza asumiendo un rango típico 0-10."""
    return max(0.0, min(100.0, priority / 10 * 100))


def _topic_potential_score(category_engagement_index: float | None) -> float:
    """Placeholder explícito hasta tener suficiente histórico (spec 18,
    Learning Loop): sin datos, se asume potencial neutro (50)."""
    return category_engagement_index if category_engagement_index is not None else 50.0


def _historical_source_performance_score(source_avg_views_percentile: float | None) -> float:
    return source_avg_views_percentile if source_avg_views_percentile is not None else 50.0


def _category_performance_score(category_avg_views_percentile: float | None) -> float:
    return category_avg_views_percentile if category_avg_views_percentile is not None else 50.0


def _early_engagement_score(early_engagement_rate: float | None) -> float:
    if early_engagement_rate is None:
        return 0.0  # sin señal aún = no suma, no resta contra lo desconocido
    return max(0.0, min(100.0, early_engagement_rate * 100))


def compute_factor_score(
    *,
    published_at: datetime | None,
    source_priority: int,
    category_engagement_index: float | None = None,
    source_avg_views_percentile: float | None = None,
    category_avg_views_percentile: float | None = None,
    early_engagement_rate: float | None = None,
    now: datetime | None = None,
) -> ScoreBreakdown:
    now = now or datetime.now(timezone.utc)
    components = {
        "recency": _recency_score(published_at, now=now),
        "source_priority": _source_priority_score(source_priority),
        "topic_potential": _topic_potential_score(category_engagement_index),
        "historical_source_performance": _historical_source_performance_score(source_avg_views_percentile),
        "category_performance": _category_performance_score(category_avg_views_percentile),
        "early_engagement": _early_engagement_score(early_engagement_rate),
    }
    weighted = {k: components[k] * WEIGHTS[k] for k in WEIGHTS}
    total = round(sum(weighted.values()))
    total = max(0, min(100, total))

    top_contributors = sorted(weighted.items(), key=lambda kv: kv[1], reverse=True)[:2]
    explanation = "; ".join(f"{name}={value:.1f}" for name, value in top_contributors)

    return ScoreBreakdown(total=total, components=components, weighted=weighted, explanation=explanation)
