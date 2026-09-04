# Test Strategy — Factor Content

## Pirámide de tests
- **Unit** (mayoría): scoring (`Factor Score`), transiciones de estado
  (`ContentItem`, `Post`, `RenderJob`), validación de `configuration_json`
  de templates (Pydantic), lógica pura de `scheduler_service`.
- **Integration**: routers FastAPI contra una BD Postgres real (contenedor
  de test), adapters de publicación contra un `MockPublisherAdapter` (no
  contra las APIs reales en CI).
- **E2E**: un happy path completo por entorno de staging/manual —
  descubrir → seleccionar → importar → renderizar → revisar → programar →
  "publicar" (mock) → ver métricas — no se corre en cada PR, sí antes de
  cada release.

## Tests obligatorios desde Phase 0
- Logging no filtra secretos: un logger de prueba recibe un dict con clave
  `api_key`/`token`/`password` y el test verifica que el output redacta el
  valor.
- `/health` y `/ready` responden 200 con Docker Compose recién levantado.
- Migraciones Alembic aplican limpio sobre BD vacía (`alembic upgrade
  head` sin errores) y son reversibles (`alembic downgrade -1` no rompe).

## Invariantes críticos (spec, sección 27) — cada uno es un test explícito
1. **Un post no puede publicarse dos veces.**
   Test: publicar el mismo `post_id` dos veces en paralelo (simulando dos
   workers) y verificar que solo una transición a `PUBLISHED` ocurre
   (usando el locking de `SELECT ... FOR UPDATE` o equivalente).
2. **Jobs fallidos pueden reintentar de forma segura.**
   Test: un `RenderJob` que falla a mitad de proceso, al reintentar, no
   deja un `MediaAsset` de salida duplicado ni corrupto (idempotencia por
   `content_item_id + template_id + version`, no por reintento ciego).
3. **Contenido aprobado no puede volverse rechazado por accidente.**
   Test: la máquina de estados de `ContentItem` rechaza transiciones
   `APPROVED → REJECTED` que no pasen por una acción explícita registrada
   en `audit_logs` (no una transición "automática" del pipeline).
4. **Posts programados no se publican antes de su hora.**
   Test: el `publish_worker` no debe recoger un post con `scheduled_at` en
   el futuro, ni con reloj adelantado en el propio worker (usar tiempo del
   servidor de BD como fuente de verdad, no reloj local del worker).
5. **Las credenciales nunca aparecen en logs.**
   Ver arriba (logging) — se repite aquí porque el spec lo lista como
   invariante crítico, no solo como buena práctica.
6. **Contenido sin rights_status aceptable no puede entrar a publicación
   automática.**
   Test: intentar programar un post desde un `ContentItem` con
   `rights_status` no aprobado debe fallar en `validate_post` del adapter
   y en la capa de servicio, no solo en la UI.

## Mocking de plataformas externas
- `MockPublisherAdapter` implementa la interfaz completa y permite simular:
  éxito, rate-limit (429), token expirado, fallo de red, y respuesta lenta
  (para probar timeouts).
- Los tests de `scheduler_service` y `publish_worker` corren exclusivamente
  contra el mock en CI. Los adapters reales (`TikTokAdapter`, etc.) tienen
  sus propios tests de integración marcados para correr solo manualmente o
  en un pipeline separado con credenciales de sandbox, nunca en CI público.

## Cobertura mínima por fase (Definition of Done de cada fase)
- Phase 0: tests de arranque + logging + migraciones (arriba).
- Phase 1: CRUD de `sources`/`content_items`, deduplicación (por
  external_id, URL canónica y checksum), transición `DISCOVERED →
  SELECTED`.
- Phase 2: validación de `configuration_json` con Pydantic, un render real
  end-to-end contra un vídeo de prueba corto, verificación de que el output
  respeta el template versionado.
- Phase 3: flujo de aprobación/rechazo, acciones bulk, edición de metadata.
- Phase 4: los 6 invariantes críticos de arriba, tests de cada adapter
  contra el mock.
- Phase 5: cálculo correcto de KPIs agregados (views/video, mediana,
  engagement rate) con datos de fixture conocidos.
- Phase 6: Factor Score determinista dado el mismo input; AI generations
  versionadas correctamente (`model` + `prompt_version` no cambian
  retroactivamente resultados ya guardados).

## Herramientas
- Backend: `pytest`, `pytest-asyncio` (si aplica), `httpx` para tests de
  API, `factory_boy` o fixtures simples para datos de prueba.
- Lint/tipos: `ruff`, `mypy`.
- Frontend: `vitest`/`jest` + `@testing-library/react` para componentes
  críticos (review screen, calendario).
- CI: todo lo anterior corre en cada PR contra `postgres`/`redis` en
  contenedores efímeros (ver `05_PHASE0_PLAN.md`, punto 10).
