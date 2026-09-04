"""Schema estricto de la configuración de ScriptTemplate. Genérico a
propósito: aún no tenemos la plantilla concreta del operador, así que
modela la forma general (secciones ordenadas + límites) sin asumir
contenido específico. Se ajusta en cuanto llegue la plantilla real."""
from pydantic import BaseModel, Field, model_validator


class ScriptSection(BaseModel):
    """Una sección del guion, en el orden en que debe aparecer.
    role típico: 'hook', 'body', 'cta' — pero es libre, igual que
    TextZone.role en la plantilla visual, para no asumir tu estructura.

    repeat=True convierte la sección en una LISTA de N textos cortos
    (ej. varios 'beats' de una historia en formato burbuja de chat) en vez
    de un único bloque — se renderiza contra un BubbleListZone con el
    mismo role."""
    role: str
    instructions: str = ""  # guía de tono/contenido para esa sección, en texto libre
    max_words: int | None = Field(default=None, gt=0)
    repeat: bool = False
    count: int | None = Field(default=None, gt=0)  # obligatorio si repeat=True

    @model_validator(mode="after")
    def count_required_if_repeat(self) -> "ScriptSection":
        if self.repeat and not self.count:
            raise ValueError(f"sección '{self.role}': repeat=True requiere count")
        return self


class ScriptTemplateConfiguration(BaseModel):
    sections: list[ScriptSection] = Field(default_factory=list, min_length=1)
    hashtag_count: int = Field(default=5, ge=0, le=30)
    keyword_count: int = Field(default=5, ge=0, le=30)
    title_max_words: int = Field(default=12, gt=0)
    tone: str = "neutral"  # ej. "urgente", "informativo", "casual" — libre
    caption_pattern: str = "title_plus_hashtags"
    # "title_plus_hashtags": caption = título + hashtags (patrón observado
    # en el ejemplo del operador). Otros valores quedan abiertos para el
    # futuro sin romper plantillas ya guardadas.
