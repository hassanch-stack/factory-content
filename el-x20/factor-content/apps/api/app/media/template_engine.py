"""Valida configuration_json contra TemplateConfiguration antes de guardar
o de renderizar. Nunca se acepta JSON libre sin pasar por aquí (spec 8)."""
from pydantic import ValidationError

from app.schemas.template_config import TemplateConfiguration


class InvalidTemplateConfigError(Exception):
    pass


def validate_configuration(raw_config: dict) -> TemplateConfiguration:
    try:
        return TemplateConfiguration.model_validate(raw_config)
    except ValidationError as exc:
        raise InvalidTemplateConfigError(str(exc)) from exc
