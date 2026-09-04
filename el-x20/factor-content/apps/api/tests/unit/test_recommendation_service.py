"""Recomendaciones deben ser explicables (spec 18) y requerir tamaño de
muestra mínimo antes de sugerir nada (evita conclusiones con 1-2 datos)."""
from unittest.mock import MagicMock

from app.services.recommendation_service import recommend_by_source


def test_no_recommendation_below_min_sample():
    db = MagicMock()
    db.execute.return_value = [(MagicMock(id="p1"), MagicMock(source_id="s1"), 100)]
    recs = recommend_by_source(db, min_sample=5)
    assert recs == []
