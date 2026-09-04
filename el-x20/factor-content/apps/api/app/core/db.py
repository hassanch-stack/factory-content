"""Engine/session de SQLAlchemy. Sync en V1 (Celery también es sync;
mantener un único modelo de concurrencia simplifica el código, ver ADR 0002)."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True, pool_size=10, max_overflow=10)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base declarativa compartida por todos los modelos."""


def get_db() -> Generator[Session, None, None]:
    """Dependency de FastAPI: una sesión por request, cerrada siempre."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
