# Factor Content — Handoff para Codex

Este repo NO es un scaffold vacío: las 6 fases del roadmap original (spec en
`docs/`) están implementadas en código — 69 archivos Python en
`apps/api/app`, 13 archivos de test, 8 migraciones Alembic. Tu trabajo es
**verificar, corregir y completar**, no diseñar desde cero.

## Regla de oro antes de tocar nada
Lee en este orden, no lo saltes:
1. `README.md` — visión general y principios del producto
2. `docs/adr/0001` a `0007` — por qué se tomó cada decisión de arquitectura
   (0007 es el pivote vídeo→foto, el más importante para entender el estado actual)
3. `docs/03_ERD.md` — modelo de datos completo
4. `docs/05_PHASE0_PLAN.md`, `06_SECURITY_CHECKLIST.md`,
   `07_PLATFORM_INTEGRATION_CHECKLIST.md`, `08_TEST_STRATEGY.md`

No has visto el spec original completo — está resumido en los ADRs y docs,
pero si algo no cuadra, los docs son la fuente de verdad, no supongas.

## Estado real (léelo con escepticismo, verifícalo tú mismo)

**Nunca se ejecutó `pytest` de verdad.** El entorno donde se escribió este
código no tenía acceso a red para instalar dependencias. Todo se verificó
con `python3 -m py_compile` (sintaxis limpia, confirmado) y, para la lógica
sin dependencias externas (`scoring_service.py`), se ejecutó manualmente a
mano fuera de pytest. **Tu primera tarea real es correr la suite completa
y arreglar lo que falle** — puede que haya imports circulares, fixtures
rotos, o errores de tipado que `py_compile` no detecta.

```bash
cd apps/api
pip install -e ".[dev]"
alembic upgrade head   # requiere Postgres real corriendo (ver infra/docker-compose.yml)
pytest -v
ruff check .
mypy app
```

## Lo que SÍ está completo y no debería rediseñarse
- Máquinas de estado de `ContentItem` y `Post` (con sus invariantes)
- Idempotencia de render (`content_item + template + template_version + slide_index`)
- Locking del scheduler (`SELECT FOR UPDATE SKIP LOCKED`)
- Pipeline de fotos con Pillow (`image_compositor.py`): zonas de texto simples
  + burbujas de chat apiladas + branding
- `PublisherAdapter` como interfaz única (`app/publishers/base.py`)
- Factor Score rule-based + recomendaciones explicables (Phase 6)
- Las 8 migraciones Alembic, en orden, con sus índices críticos

## Lo que está deliberadamente INCOMPLETO — aquí es donde trabajas

### 1. TikTok/Instagram/Facebook adapters (prioridad alta)
`app/publishers/tiktok.py`, `instagram.py`, `facebook.py` son **stubs que
lanzan `NotImplementedError`** a propósito. Antes de implementarlos:
- Lee `docs/07_PLATFORM_INTEGRATION_CHECKLIST.md` completo
- Verifica la documentación oficial VIGENTE de cada API (cambia con
  frecuencia) — no uses conocimiento previo sin confirmar fecha de consulta
- Implementa contra `MockPublisherAdapter` como referencia de contrato
  (`app/publishers/mock.py`) — la interfaz ya está bien definida, solo
  falta la implementación real
- Los métodos ahora reciben `media_paths: list[str]` (soporte de carrusel
  añadido tras el ejemplo real del operador — ver ADR implícito en el
  historial de `render_job.py`, campo `slide_index`)

### 2. Radar (Sources → Content Queue) — NO implementado
El spec original (sección 5.1/22) pide un módulo Radar que haga polling de
fuentes y cree `ContentItem`s automáticamente. **Esto nunca se construyó.**
Existen los modelos (`Source`, `SourceCheck`, `ContentItem`) y el servicio
de deduplicación (`dedup_service.py`), pero no hay:
- Lógica de polling/scraping real de ninguna fuente
- La tarea Celery periódica de radar (el `beat_schedule.py` solo tiene
  `publish` y `analytics`, falta `radar`)
- El cálculo automático de Factor Score al descubrir contenido nuevo
  (`scoring_service.py` existe pero nadie lo llama desde un flujo de radar)

Esto probablemente es el trabajo más grande que falta. Empieza aquí si el
objetivo es tener el sistema operando de punta a punta.

### 3. Tests de integración — necesitan Postgres real para correr
`tests/integration/test_scheduler_invariants.py` usa un fixture
`db_session` (`tests/integration/conftest.py`) que crea/destruye el schema
completo. Nunca se ejecutó contra una BD real. Verifica que:
- Los fixtures (`approved_content_item`, `account`) no tengan bugs
- El test de idempotencia de publish (`test_publish_post_is_idempotent`)
  realmente pase

### 4. Auth — mencionada pero no cableada
`docs/05_PHASE0_PLAN.md` pide Supabase Auth o similar. El middleware que
exige token válido en todos los routers (salvo `/health`) **no está
implementado**. Ahora mismo cualquier endpoint es público. No lo dejes así
si esto va a producción.

### 5. Prompt de IA — nunca se probó contra el modelo real
`app/services/ai_service.py` tiene el prompt completo y el schema de
validación (`ScriptOutput`), pero nunca se hizo una llamada real a la API
de Anthropic (no había `ANTHROPIC_API_KEY` disponible en el entorno donde
se escribió). Antes de confiar en el pipeline completo, genera 5-10
ejemplos reales y verifica que el JSON que devuelve el modelo:
- Siempre valida contra `ScriptOutput`
- Respeta `repeat`/`count` en las secciones (debe devolver listas, no
  strings, para `body_beats`)
- No inventa hechos ni presenta acusaciones como verdad (regla explícita
  en el system prompt — verifícala con casos de contenido sensible reales)

### 6. Frontend — solo 2 páginas, sin auth, sin manejo de errores real
`apps/web/app/dashboard` y `apps/web/app/review` son funcionales pero
mínimos. Faltan: `/queue`, `/editor`, `/calendar`, `/accounts`, `/sources`,
`/templates`, `/analytics`, `/settings`, `/jobs` (todas mencionadas en
`docs/` sección de dashboard, ninguna construida aún salvo las 2 dichas).

## Plantilla ya confirmada por el operador — úsala tal cual
`examples/script_template.json`, `examples/template_visual_hook_slide.json`,
`examples/template_visual_body_slide.json` son la plantilla REAL confirmada
(no un placeholder): carrusel de 2 slides, hook + 3 beats de máx. 25
palabras + CTA + 5 hashtags. Súbelas vía `POST /api/script-templates` y
`POST /api/templates` como parte del seed inicial — no inventes una
plantilla distinta.

## Advertencia operativa (no técnica, pero relevante para lo que construyas)
Este sistema está pensado para producir contenido de noticias/shock a
escala automatizada. El propio spec y el prompt de IA ya incluyen la regla
de "nunca presentar acusaciones no verificadas como hechos" — mantenla
intacta si tocas `ai_service.py`. Si añades el módulo de Radar, considera
que cualquier fuente con `permission_status=UNKNOWN` **nunca** debe
procesarse automáticamente (ya está en el modelo `Source.can_be_auto_processed()`,
pero nadie lo está llamando todavía porque no existe el Radar — no lo
saltes cuando lo construyas).

## Orden sugerido de trabajo
1. Levanta el entorno (`docker compose up -d`, `alembic upgrade head`) y
   corre la suite de tests real — arregla lo que falle antes de construir
   nada nuevo encima de una base no verificada.
2. Construye el Radar (punto 2 arriba) — sin esto el sistema no tiene
   forma de recibir contenido nuevo.
3. Implementa un adapter real (empieza por el que tengas credenciales de
   sandbox disponibles) siguiendo el checklist de plataforma.
4. Cablea auth.
5. Completa las páginas de frontend que falten, según lo necesites operar.
