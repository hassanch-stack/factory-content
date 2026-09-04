"""Tests de ai_service — la IA nunca debe persistir output que no valide
contra ScriptOutput (spec 10: nunca texto libre sin estructura)."""
from unittest.mock import patch

import pytest

from app.services.ai_service import AIGenerationError, rewrite_script


class _FakeContentItem:
    title = "Título de prueba"
    description = "Descripción de prueba"
    category = "noticias"


def test_rejects_non_json_llm_output():
    with patch("app.services.ai_service._call_llm", return_value="esto no es json"):
        with pytest.raises(AIGenerationError):
            rewrite_script(_FakeContentItem(), {"sections": [{"role": "hook"}]})


def test_rejects_json_missing_required_fields():
    with patch("app.services.ai_service._call_llm", return_value='{"hook": "solo esto"}'):
        with pytest.raises(AIGenerationError):
            rewrite_script(_FakeContentItem(), {"sections": [{"role": "hook"}]})


def test_accepts_well_formed_output():
    valid_json = (
        '{"hook": "h", "sections": {"body": "texto"}, "cta": "c", '
        '"title": "t", "hashtags": ["#a"], "keywords": ["k"]}'
    )
    with patch("app.services.ai_service._call_llm", return_value=valid_json):
        result = rewrite_script(_FakeContentItem(), {"sections": [{"role": "hook"}]})
    assert result.hook == "h"
    assert result.hashtags == ["#a"]


def test_rejects_rewrite_without_original_script():
    item = _FakeContentItem()
    item.description = ""
    with pytest.raises(AIGenerationError, match="guion original"):
        rewrite_script(item, {"sections": [{"role": "hook"}]})
