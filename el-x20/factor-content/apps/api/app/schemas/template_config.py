"""Schema estricto de configuration_json para plantillas de FOTO (spec 8,
adaptado al pivote vídeo->foto). Cada 'zone' es un área de texto sobre la
imagen (hook, título, CTA, etc.) — el nombre/rol de cada zona lo define el
operador según su plantilla visual concreta, no está hardcodeado."""
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class CanvasConfig(BaseModel):
    width: int = Field(gt=0, le=8000)
    height: int = Field(gt=0, le=8000)
    background_fit: Literal["cover", "contain"] = "cover"


class TextZone(BaseModel):
    """Una zona de texto sobre la foto. 'role' es libre (hook, cta, title,
    headline, custom...) — el AI service rellena el contenido según el rol,
    el compositor solo dibuja lo que le llega en ese rol."""
    role: str
    enabled: bool = True
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    max_width: int = Field(gt=0)
    font_size: int = Field(default=48, gt=0, le=300)
    font_color: str = "#FFFFFF"
    align: Literal["left", "center", "right"] = "center"
    style: Literal["box", "outline"] = "box"
    # style="box": caja semitransparente detrás del texto
    box_enabled: bool = True
    box_color: str = "#000000"
    box_opacity: float = Field(default=0.55, ge=0.0, le=1.0)
    # style="outline": texto con contorno, sin caja (ej. slide de hook tipo Impact)
    outline_color: str = "#000000"
    outline_width: int = Field(default=3, ge=0, le=20)


class BubbleListZone(BaseModel):
    """Lista de 'burbujas de chat' apiladas verticalmente — una por cada
    elemento de una sección repetible del guion (ScriptSection.repeat=True).
    role debe coincidir con esa sección para que el compositor sepa qué
    lista de textos dibujar aquí."""
    role: str
    enabled: bool = True
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    max_width: int = Field(gt=0)
    font_size: int = Field(default=42, gt=0, le=200)
    font_color: str = "#FFFFFF"
    bubble_color: str = "#4A4A4A"
    bubble_opacity: float = Field(default=0.85, ge=0.0, le=1.0)
    corner_radius: int = Field(default=30, ge=0, le=100)
    spacing: int = Field(default=24, ge=0)  # espacio vertical entre burbujas
    align: Literal["left", "center", "right"] = "center"


class BrandingConfig(BaseModel):
    enabled: bool = False
    logo_asset_key: str | None = None
    position: Literal["top-left", "top-right", "bottom-left", "bottom-right"] = "bottom-right"

    @model_validator(mode="after")
    def logo_required_if_enabled(self) -> "BrandingConfig":
        if self.enabled and not self.logo_asset_key:
            raise ValueError("branding.enabled=true requiere logo_asset_key")
        return self


class OutputConfig(BaseModel):
    format: Literal["jpg", "png"] = "jpg"
    quality: int = Field(default=90, ge=1, le=100)  # solo aplica a jpg


class TemplateConfiguration(BaseModel):
    """Configuración completa de una plantilla visual de foto."""

    canvas: CanvasConfig
    zones: list[TextZone] = Field(default_factory=list)
    bubble_lists: list[BubbleListZone] = Field(default_factory=list)
    branding: BrandingConfig = BrandingConfig()
    output: OutputConfig = OutputConfig()

    @model_validator(mode="after")
    def zone_roles_unique(self) -> "TemplateConfiguration":
        roles = [z.role for z in self.zones] + [b.role for b in self.bubble_lists]
        if len(roles) != len(set(roles)):
            raise ValueError("Cada role (zones + bubble_lists) debe ser único dentro de la plantilla")
        return self
