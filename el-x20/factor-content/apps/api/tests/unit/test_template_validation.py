"""Tests de validación de configuration_json para plantillas de FOTO
(spec sección 8, adaptado tras el pivote vídeo->foto)."""
import pytest
from pydantic import ValidationError

from app.schemas.template_config import TemplateConfiguration


def test_valid_minimal_config():
    config = TemplateConfiguration.model_validate({"canvas": {"width": 1080, "height": 1920}})
    assert config.canvas.width == 1080
    assert config.zones == []


def test_rejects_canvas_out_of_range():
    with pytest.raises(ValidationError):
        TemplateConfiguration.model_validate({"canvas": {"width": 999999, "height": 1920}})


def test_rejects_missing_canvas():
    with pytest.raises(ValidationError):
        TemplateConfiguration.model_validate({"zones": []})


def test_branding_enabled_requires_logo():
    with pytest.raises(ValidationError):
        TemplateConfiguration.model_validate({
            "canvas": {"width": 1080, "height": 1920},
            "branding": {"enabled": True},
        })


def test_branding_enabled_with_logo_ok():
    config = TemplateConfiguration.model_validate({
        "canvas": {"width": 1080, "height": 1920},
        "branding": {"enabled": True, "logo_asset_key": "branding/logo.png"},
    })
    assert config.branding.logo_asset_key == "branding/logo.png"


def test_zone_roles_must_be_unique():
    with pytest.raises(ValidationError):
        TemplateConfiguration.model_validate({
            "canvas": {"width": 1080, "height": 1920},
            "zones": [
                {"role": "hook", "x": 0, "y": 0, "max_width": 500},
                {"role": "hook", "x": 0, "y": 600, "max_width": 500},
            ],
        })


def test_multiple_distinct_zones_ok():
    config = TemplateConfiguration.model_validate({
        "canvas": {"width": 1080, "height": 1920},
        "zones": [
            {"role": "hook", "x": 40, "y": 100, "max_width": 1000},
            {"role": "cta", "x": 40, "y": 1700, "max_width": 1000},
        ],
    })
    assert {z.role for z in config.zones} == {"hook", "cta"}
