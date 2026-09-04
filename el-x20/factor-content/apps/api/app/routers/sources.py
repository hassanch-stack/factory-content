import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceOut, SourceUpdate

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)) -> list[Source]:
    return list(db.scalars(select(Source).order_by(Source.priority.desc())))


@router.post("", response_model=SourceOut, status_code=201)
def create_source(payload: SourceCreate, db: Session = Depends(get_db)) -> Source:
    source = Source(**payload.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.get("/{source_id}", response_model=SourceOut)
def get_source(source_id: uuid.UUID, db: Session = Depends(get_db)) -> Source:
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(404, "Source no encontrada")
    return source


@router.patch("/{source_id}", response_model=SourceOut)
def update_source(source_id: uuid.UUID, payload: SourceUpdate, db: Session = Depends(get_db)) -> Source:
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(404, "Source no encontrada")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(source, field, value)
    db.commit()
    db.refresh(source)
    return source
