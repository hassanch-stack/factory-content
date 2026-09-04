"""Endpoints de Phase 6: Factor Score bajo demanda y recomendaciones del
Learning Loop. No hay endpoint de 'entrenar modelo' — V1 es rule-based
(spec 17/18), a propósito."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.content_item import ContentItem
from app.models.source import Source
from app.schemas.scoring import RecommendationOut, ScoreBreakdownOut
from app.services.recommendation_service import recommend_by_category, recommend_by_source
from app.services.scoring_service import compute_factor_score

router = APIRouter(prefix="/api/analytics", tags=["intelligence"])


@router.post("/content/{content_item_id}/recalculate-score", response_model=ScoreBreakdownOut)
def recalculate_score(content_item_id: uuid.UUID, db: Session = Depends(get_db)) -> ScoreBreakdownOut:
    item = db.get(ContentItem, content_item_id)
    if not item:
        raise HTTPException(404, "Content item no encontrado")
    source = db.get(Source, item.source_id)

    breakdown = compute_factor_score(
        published_at=item.published_at,
        source_priority=source.priority if source else 0,
    )
    item.factor_score = breakdown.total
    db.commit()

    return ScoreBreakdownOut(
        total=breakdown.total, components=breakdown.components,
        weighted=breakdown.weighted, explanation=breakdown.explanation,
    )


@router.get("/recommendations", response_model=list[RecommendationOut])
def get_recommendations(db: Session = Depends(get_db)) -> list[RecommendationOut]:
    recs = recommend_by_source(db) + recommend_by_category(db)
    return [
        RecommendationOut(
            dimension=r.dimension, entity_label=r.entity_label,
            multiplier=r.multiplier, sample_size=r.sample_size, explanation=r.explanation,
        )
        for r in recs
    ]
