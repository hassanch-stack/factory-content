# ADR 0004 — FFmpeg como único motor de renderizado

**Estado:** Aceptado

## Contexto
Factor Content necesita conversión 9:16, crop/reframe, resize, trim,
concatenación, normalización de audio, subtítulos, overlays de texto,
branding opcional, intro/outro y extracción de thumbnails, todo en bulk.

## Decisión
FFmpeg/ffprobe como motor de bajo nivel, ejecutado desde los `render_worker`.
Factor Content **no** construye un editor/codec propio (explícitamente
prohibido en el spec, punto 7): la propiedad intelectual del producto está
en el `template_engine` (orquestación data-driven) y no en el procesamiento
de vídeo en sí.

## Razones
- FFmpeg cubre el 100% de las operaciones V1 requeridas y es gratuito,
  auto-hospedable, sin coste por vídeo procesado (ver ADR 0006, control de
  costes).
- `ffprobe` da metadata técnica (duración, resolución, codecs) necesaria
  para `MediaAsset`.

## Alternativas consideradas
- **APIs de render cloud (Shotstack, Creatomate, etc.)**: rechazadas como
  motor principal en V1 por coste variable por vídeo (750 vídeos/mes con
  facturación por render sale caro) y porque el spec pide explícitamente
  minimizar costes variables (punto 32). Pueden evaluarse más adelante como
  fallback opcional detrás de la misma interfaz de `render_service`, si el
  volumen de plantillas complejas lo justifica.

## Consecuencias
- El servidor de render necesita CPU suficiente (encoding H.264); se
  dimensiona en el Docker Compose / infraestructura, no en el diseño de
  aplicación.
- Los templates (`configuration_json`) deben mapear 1:1 a comandos/filtros
  FFmpeg deterministas y versionados (punto 8 del spec).
