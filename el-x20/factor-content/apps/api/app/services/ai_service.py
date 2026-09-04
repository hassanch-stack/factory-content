"""Reescribe un guion original (hook/secciones/CTA/título/hashtags/
keywords) a partir de un ContentItem + un ScriptTemplate.

Reglas duras del spec (sección 10), sin excepción:
- la IA no inventa hechos, citas ni cifras que no estén en el
  content_item original (título/descripción/metadata)
- el output se valida contra un schema estricto (ScriptOutput) antes de
  guardarse — nunca se persiste texto libre sin estructura
- cada generación se guarda con model + prompt_version, y es editable

PROMPT_VERSION se sube manualmente cada vez que cambia el prompt de forma
que afecte al resultado — así el historial de generaciones queda trazable.
"""
import json

from pydantic import ValidationError

from app.core.config import get_settings
from app.schemas.ai_generation import ScriptOutput

PROMPT_VERSION = "v1"
MODEL_NAME = "claude-sonnet-4-6"

_SYSTEM_PROMPT = """Eres un editor de contenido para redes sociales. Recibes:
1. Un guion o texto original aportado por el operador, ya verificado.
2. Una plantilla de guion con secciones específicas y sus instrucciones de tono.

Tu tarea: REESCRIBIR exclusivamente ese texto siguiendo EXACTAMENTE la
estructura de secciones pedida. No crees un guion nuevo ni añadas detalles
que no aparezcan en el texto original.

REGLAS ESTRICTAS:
- NUNCA inventes hechos, cifras, citas o afirmaciones que no estén en el
  contenido original. Si falta información para una sección, sé general
  en vez de inventar datos.
- NUNCA presentes una acusación, rumor o hipótesis no confirmada como si
  fuera un hecho verificado. Si el contenido original incluye una
  acusación o versión de alguien, atribúyela explícitamente a esa fuente
  (ej. "según su versión...", "afirma que...") — no la reformules como
  verdad establecida.
- Responde ÚNICAMENTE con un JSON válido, sin texto adicional, con esta forma:
{
  "hook": "...",
  "sections": {"<role_de_seccion>": "..." o ["...", "...", "..."] si la sección es repetible, ...},
  "cta": "...",
  "title": "...",
  "hashtags": ["...", ...],
  "keywords": ["...", ...]
}
Para una sección marcada como repetible (repeat=True, con un "count" N),
"sections"["<role>"] debe ser una LISTA de exactamente N strings cortos
(uno por cada beat/burbuja), no un único bloque de texto.
"""


class AIGenerationError(Exception):
    pass


def _build_user_prompt(content_item, script_template_config: dict) -> str:
    sections_desc = "\n".join(
        f"- role='{s['role']}'"
        + (f", REPETIBLE: generar exactamente {s['count']} beats cortos" if s.get("repeat") else "")
        + (f", máx {s['max_words']} palabras cada uno" if s.get("max_words") else "")
        + (f". Instrucciones: {s['instructions']}" if s.get("instructions") else "")
        for s in script_template_config.get("sections", [])
    )
    return f"""GUION ORIGINAL A REESCRIBIR:
{content_item.description}

Título de referencia: {content_item.title or "(sin título)"}
Categoría: {content_item.category or "(sin categoría)"}

ESTRUCTURA DE SECCIONES PEDIDA:
{sections_desc}

Tono general: {script_template_config.get("tone", "neutral")}
Número de hashtags a generar: {script_template_config.get("hashtag_count", 5)}
Número de keywords a generar: {script_template_config.get("keyword_count", 5)}
Título: máximo {script_template_config.get("title_max_words", 12)} palabras.
"""


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """Aísla la llamada real al API de Anthropic. Separado para poder
    mockearlo en tests sin gastar tokens ni requerir ANTHROPIC_API_KEY."""
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise AIGenerationError("ANTHROPIC_API_KEY no configurada")

    import anthropic  # import local: no es dependencia dura del resto de la app

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def rewrite_script(content_item, script_template_config: dict) -> ScriptOutput:
    """Reescribe un guion aportado por el operador.

    Lanza AIGenerationError si no hay texto original o si el LLM devuelve
    algo que no valida contra ScriptOutput — nunca se guarda output
    malformado ni texto libre sin estructura."""
    if not content_item.description or not content_item.description.strip():
        raise AIGenerationError("Debes aportar el guion original que quieres reescribir.")
    user_prompt = _build_user_prompt(content_item, script_template_config)
    raw = _call_llm(_SYSTEM_PROMPT, user_prompt)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AIGenerationError(f"El LLM no devolvió JSON válido: {exc}") from exc

    try:
        return ScriptOutput.model_validate(parsed)
    except ValidationError as exc:
        raise AIGenerationError(f"El output no cumple el schema esperado: {exc}") from exc


# Alias temporal para no romper integraciones internas anteriores. La
# operación siempre aplica las mismas reglas de reescritura, no generación.
generate_script = rewrite_script
