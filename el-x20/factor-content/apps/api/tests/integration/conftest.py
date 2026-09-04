"""Fixture de sesión de BD para tests de integración — requiere Postgres
real (CI lo levanta como servicio, ver .github/workflows/ci.yml). Cada
test corre en una transacción que se revierte al final, así los tests no
se contaminan entre sí ni dejan basura en la BD de test."""
import pytest
from sqlalchemy.orm import sessionmaker

from app.core.db import Base, engine


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
