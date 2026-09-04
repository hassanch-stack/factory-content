from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.post import PostOut, ScheduleCreate
from app.services import scheduler_service

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


@router.post("", response_model=PostOut, status_code=201)
def create_schedule(payload: ScheduleCreate, db: Session = Depends(get_db)):
    try:
        post = scheduler_service.schedule_post(
            db,
            content_item_id=payload.content_item_id,
            account_id=payload.account_id,
            platform=payload.platform,
            scheduled_at=payload.scheduled_at,
        )
    except scheduler_service.SchedulerError as exc:
        raise HTTPException(422, str(exc)) from exc
    return post
