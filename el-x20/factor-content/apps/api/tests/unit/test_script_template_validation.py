"""Tests de validación de la plantilla de GUION (estructura genérica hasta
que el operador aporte su plantilla concreta)."""
import pytest
from pydantic import ValidationError

from app.schemas.script_template_config import ScriptTemplateConfiguration


def test_valid_config_with_sections():
    config = ScriptTemplateConfiguration.model_validate({
        "sections": [
            {"role": "hook", "max_words": 20},
            {"role": "body", "max_words": 80, "instructions": "tono urgente"},
        ],
        "hashtag_count": 8,
        "keyword_count": 6,
    })
    assert len(config.sections) == 2
    assert config.hashtag_count == 8


def test_requires_at_least_one_section():
    with pytest.raises(ValidationError):
        ScriptTemplateConfiguration.model_validate({"sections": []})


def test_defaults_are_sane():
    config = ScriptTemplateConfiguration.model_validate({"sections": [{"role": "hook"}]})
    assert config.tone == "neutral"
    assert config.title_max_words == 12
