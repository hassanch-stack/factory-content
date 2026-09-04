"""Learning Loop — spec sección 18. V1: comparaciones estadísticas simples
y explicables sobre datos propios (source/categoría/plantilla/cuenta/
horario vs. performance histórica), NO un modelo entrenado. El spec pide
explícitamente 'Recommendations should be explainable' y 'Do not
prematurely build machine learning' — este servicio es la versión más
simple que cumple ambas cosas: medianas comparadas contra la mediana
global, con el múltiplo como explicación (ej. spec: 'Source A performs
2.4x better than the account median')."""
from dataclasses import dataclass
from statistics import median

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content_item import ContentItem
from app.models.post import Post
from app.models.post_metrics import PostMetrics


@dataclass
class Recommendation:
    dimension: str  # "source" | "category" | "template" | "account" | "posting_window"
    entity_label: str
    multiplier: float  # ej. 2.4 = 2.4x la mediana
    sample_size: int
    explanation: str


def _latest_views_per_post(db: Session) -> list[tuple[Post, ContentItem, int]]:
    """Une Post + ContentItem + última métrica de views. Sirve de base
    para todas las comparaciones de esta capa."""
    query = (
        select(Post, ContentItem, PostMetrics.views)
        .join(ContentItem, Post.content_item_id == ContentItem.id)
        .join(PostMetrics, PostMetrics.post_id == Post.id)
        .order_by(PostMetrics.collected_at.desc())
    )
    seen_posts = set()
    results = []
    for post, content_item, views in db.execute(query):
        if post.id in seen_posts:
            continue  # solo la métrica más reciente por post
        seen_posts.add(post.id)
        results.append((post, content_item, views))
    return results


def recommend_by_source(db: Session, *, min_sample: int = 5) -> list[Recommendation]:
    rows = _latest_views_per_post(db)
    if len(rows) < min_sample:
        return []

    global_median = median(v for _, _, v in rows)
    if global_median == 0:
        return []

    by_source: dict[str, list[int]] = {}
    for _, content_item, views in rows:
        by_source.setdefault(str(content_item.source_id), []).append(views)

    recs = []
    for source_id, views_list in by_source.items():
        if len(views_list) < min_sample:
            continue
        source_median = median(views_list)
        multiplier = round(source_median / global_median, 2)
        if multiplier >= 1.3 or multiplier <= 0.7:  # solo señales con diferencia notable
            recs.append(Recommendation(
                dimension="source",
                entity_label=source_id,
                multiplier=multiplier,
                sample_size=len(views_list),
                explanation=(
                    f"Los posts de esta fuente rinden {multiplier}x la mediana general "
                    f"(n={len(views_list)})"
                ),
            ))
    return sorted(recs, key=lambda r: r.multiplier, reverse=True)


def recommend_by_category(db: Session, *, min_sample: int = 5) -> list[Recommendation]:
    rows = _latest_views_per_post(db)
    if len(rows) < min_sample:
        return []

    global_median = median(v for _, _, v in rows)
    if global_median == 0:
        return []

    by_category: dict[str, list[int]] = {}
    for _, content_item, views in rows:
        if not content_item.category:
            continue
        by_category.setdefault(content_item.category, []).append(views)

    recs = []
    for category, views_list in by_category.items():
        if len(views_list) < min_sample:
            continue
        cat_median = median(views_list)
        multiplier = round(cat_median / global_median, 2)
        if multiplier >= 1.3 or multiplier <= 0.7:
            recs.append(Recommendation(
                dimension="category",
                entity_label=category,
                multiplier=multiplier,
                sample_size=len(views_list),
                explanation=(
                    f"La categoría '{category}' rinde {multiplier}x la mediana general "
                    f"(n={len(views_list)})"
                ),
            ))
    return sorted(recs, key=lambda r: r.multiplier, reverse=True)
