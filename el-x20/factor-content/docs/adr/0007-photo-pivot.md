# ADR 0007 — Pivote de vídeo a foto + IA de reescritura de guion

**Estado:** Aceptado
**Fecha:** Post-Phase 2

## Contexto
El producto original (spec V1) procesaba vídeo corto vía FFmpeg. El
operador decidió que Factor Content procese **solo fotos**, no vídeo, y
que la IA no solo genere metadata corta (hook/caption/hashtags como en el
spec original), sino que **reescriba el guion completo**: hook, cuerpo
por secciones, CTA, título, hashtags y palabras clave, siguiendo una
plantilla de estructura que el operador aporta.

## Decisión
1. El motor de render pasa de FFmpeg a un **compositor de imágenes**
   (`app/media/image_compositor.py`, sobre Pillow): ajusta la foto al
   canvas y dibuja "zonas de texto" (`TextZone`) definidas en una plantilla
   visual versionada — mismo patrón data-driven que tenía el `Template` de
   vídeo, adaptado a foto.
2. Se separan dos conceptos de plantilla, porque el operador los piensa
   por separado:
   - **`Template`** (visual): canvas, zonas de texto, branding, formato de
     salida — dónde y cómo se ve el texto sobre la foto.
   - **`ScriptTemplate`** (guion): secciones a generar, tono, cuántos
     hashtags/keywords, límites de palabras — qué debe escribir la IA.
3. `AIGeneration` (ya prevista en el ERD original, ahora implementada
   antes de Phase 6) conecta un `ContentItem` + un `ScriptTemplate` con el
   resultado validado (`ScriptOutput`), versionado por `model` +
   `prompt_version`, y siempre editable por el operador.
4. Reglas del spec original que se mantienen sin excepción tras el
   pivote: la IA nunca inventa hechos/cifras/citas fuera del contenido
   original, el output nunca se persiste sin pasar por un schema
   estricto, y toda generación es editable.

## Qué NO cambió (reutilizado tal cual)
Sources, Content Queue, deduplicación, máquina de estados de
`ContentItem`, storage S3/R2, scheduler, publisher adapters — ninguno de
estos módulos conocía detalles de "vídeo" específicamente; su contrato ya
era agnóstico al tipo de medio.

## Alternativas consideradas
- **Mantener FFmpeg y tratar la foto como "vídeo de 1 frame"**: rechazado
  — añade complejidad y dependencias (ffmpeg, codecs) innecesarias para
  un caso que Pillow resuelve de forma más simple y con menos superficie
  de fallo.
- **Un solo modelo de "Template" con un campo `media_type`**: rechazado
  por ahora — separar `Template` (visual) de `ScriptTemplate` (guion)
  refleja mejor que son dos plantillas que el operador gestiona y versiona
  de forma independiente (puede cambiar el guion sin tocar el diseño
  visual, y viceversa).

## Consecuencias
- `ffmpeg_runner.py` y sus tests se eliminan del repo.
- El Dockerfile del API/worker ya no instala `ffmpeg`, solo las
  librerías de sistema que necesita Pillow (`libjpeg`, `zlib`).
- `pyproject.toml` añade `Pillow` y `anthropic` (cliente oficial, usado
  por `ai_service.py`).
- Pendiente: en cuanto el operador aporte su plantilla de guion concreta,
  puede que `ScriptTemplateConfiguration` necesite campos adicionales
  específicos de esa plantilla — el schema actual es intencionalmente
  genérico para no asumir su forma exacta.
