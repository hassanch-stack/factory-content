import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.post_metrics import PostMetrics
from app.schemas.analytics import DashboardKPIs, PostMetricsOut
from app.services.analytics_service import dashboard_kpis

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview", response_model=DashboardKPIs)
def overview(account_id: uuid.UUID | None = None, db: Session = Depends(get_db)) -> DashboardKPIs:
    return DashboardKPIs(**dashboard_kpis(db, account_id=account_id))


@router.get("/posts/{post_id}/metrics", response_model=list[PostMetricsOut])
def post_metrics_history(post_id: uuid.UUID, db: Session = Depends(get_db)):
    return list(
        db.scalars(
            select(PostMetrics).where(PostMetrics.post_id == post_id).order_by(PostMetrics.collected_at)
        )
    )
