"""Recolección y agregación de métricas — spec sección 16. La normalización
por plataforma vive aquí (no en el adapter, no en el router): el adapter
solo trae el dato crudo vía get_post_metrics(); este servicio decide cómo
mapear campos específicos de cada plataforma a las columnas comunes."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.post import Post, PostStatus
from app.models.post_metrics import PostMetrics
from app.publishers.base import PublisherAdapter

# Intervalos de recolección del spec 22: 15m, 1h, 6h, 24h, 48h desde la
# publicación. Se usa para decidir qué posts tocan collect en cada pasada.
COLLECTION_OFFSETS_MINUTES = [15, 60, 360, 1440, 2880]


def _normalize(platform: str, raw: dict) -> dict:
    """Traduce el payload crudo de cada plataforma a las columnas comunes
    de PostMetrics. Placeholder explícito: los nombres de campo reales de
    TikTok/Instagram/Facebook se confirman al implementar cada adapter
    (docs/07_PLATFORM_INTEGRATION_CHECKLIST.md) — aquí se asume que
    get_post_metrics() ya devuelve estas claves comunes, tal como las
    define MockPublisherAdapter."""
    return {
        "views": raw.get("views", 0),
        "likes": raw.get("likes", 0),
        "comments": raw.get("comments", 0),
        "shares": raw.get("shares", 0),
        "saves": raw.get("saves", 0),
        "watch_time_ms": raw.get("watch_time_ms", 0),
        "completion_rate": raw.get("completion_rate", 0.0),
        "followers_gained": raw.get("followers_gained", 0),
    }


def collect_metrics_for_post(db: Session, post_id, *, adapter: PublisherAdapter) -> PostMetrics:
    post = db.get(Post, post_id)
    if not post or not post.external_post_id:
        raise ValueError("Post no encontrado o sin external_post_id (aún no publicado)")

    raw = adapter.get_post_metrics(external_post_id=post.external_post_id, credential_payload={})
    normalized = _normalize(post.platform, raw)

    metric = PostMetrics(post_id=post.id, raw_platform_data=raw, **normalized)
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


def posts_due_for_collection(db: Session, *, now: datetime | None = None) -> list[Post]:
    """Posts PUBLISHED cuya última recolección corresponde a alguno de los
    offsets configurados (evita llamadas excesivas a la API — spec 22:
    'avoid excessive API calls')."""
    now = now or datetime.now(timezone.utc)
    due: list[Post] = []

    posts = db.scalars(select(Post).where(Post.status == PostStatus.PUBLISHED))
    for post in posts:
        if not post.published_at:
            continue
        elapsed_minutes = (now - post.published_at).total_seconds() / 60

        collections_so_far = db.scalar(
            select(func.count()).select_from(PostMetrics).where(PostMetrics.post_id == post.id)
        )

        for i, offset in enumerate(COLLECTION_OFFSETS_MINUTES):
            if elapsed_minutes >= offset and collections_so_far <= i:
                due.append(post)
                break

    return due


def dashboard_kpis(db: Session, *, account_id=None) -> dict:
    """KPIs del dashboard (spec 16): total views, views/vídeo->foto,
    mediana, engagement rate, completion rate, followers ganados, mejor
    fuente/categoría/plantilla/cuenta/horario."""
    query = select(PostMetrics).join(Post, PostMetrics.post_id == Post.id)
    if account_id:
        query = query.where(Post.account_id == account_id)

    metrics = list(db.scalars(query))
    if not metrics:
        return {
            "total_views": 0, "views_per_post": 0, "median_views": 0,
            "engagement_rate": 0.0, "avg_completion_rate": 0.0, "followers_gained": 0,
        }

    views = sorted(m.views for m in metrics)
    total_views = sum(views)
    total_engagement = sum(m.likes + m.comments + m.shares + m.saves for m in metrics)

    return {
        "total_views": total_views,
        "views_per_post": total_views / len(metrics),
        "median_views": views[len(views) // 2],
        "engagement_rate": (total_engagement / total_views) if total_views else 0.0,
        "avg_completion_rate": sum(m.completion_rate for m in metrics) / len(metrics),
        "followers_gained": sum(m.followers_gained for m in metrics),
    }
