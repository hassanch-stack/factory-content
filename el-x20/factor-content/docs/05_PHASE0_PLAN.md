# Phase 0 — Project Foundation: plan de implementación

Objetivo: que `docker compose up -d && make migrate && make seed` funcione
de punta a punta, con un endpoint `/health` respondiendo, auth mínima
funcionando y CI corriendo tests vacíos-pero-reales, **antes** de tocar
ninguna lógica de negocio (Sources, Content Queue, etc. son Phase 1).

## Tareas, en orden

1. **Repositorio**
   - Inicializar monorepo con la estructura de `01_REPO_TREE.md`.
   - `.gitignore` (incluye `.env`, `__pycache__`, `node_modules`, `*.mp4` en
     carpetas de trabajo local).
   - `README.md` con instrucciones de arranque.

2. **Docker Compose**
   - `infra/docker-compose.yml` (ya provisto) + `infra/.env.example`.
   - Verificar que `postgres`, `redis` y `minio` levantan con healthcheck OK.

3. **FastAPI esqueleto**
   - `apps/api/app/main.py` con `/health` y `/ready`.
   - `apps/api/app/core/config.py` (pydantic-settings, lee `.env`).
   - `apps/api/app/core/db.py` (engine SQLAlchemy async o sync — decidir
     sync en V1 para simplicidad, Celery también es sync).
   - `apps/api/pyproject.toml` con dependencias fijadas.

4. **Next.js esqueleto**
   - `apps/web` con una sola página que haga `fetch` a `/health` del API,
     para validar conectividad end-to-end desde el día 1.
   - Tailwind configurado, sin librería de componentes todavía (regla del
     spec: "solo si mejora velocidad, no sobre-ingeniería").

5. **PostgreSQL + Alembic**
   - `apps/api/alembic/` inicializado, apuntando a `DATABASE_URL`.
   - Primera migración: solo tabla `users` (para auth) + `system_settings`.
     El resto de tablas del ERD llegan en Phase 1/2 con sus módulos.

6. **Redis + Celery esqueleto**
   - `workers/celery_app.py` configurado con las 7 colas nombradas pero
     sin tareas reales todavía (una tarea `ping` de humo).
   - `workers/beat_schedule.py` vacío, listo para añadir radar/analytics en
     fases posteriores.

7. **Auth**
   - Integrar Supabase Auth (o proveedor equivalente) en vez de construir
     hashing de contraseñas propio (regla explícita del spec, sección 3).
   - Un único rol `admin` en V1 (single-user), preparado para roles
     adicionales después.
   - Middleware de FastAPI que exige token válido en todos los routers
     salvo `/health`, `/ready`, `/api/auth/*`.

8. **Logging estructurado**
   - `apps/api/app/core/logging.py`: JSON logs con `timestamp`, `job_id`
     (o `request_id`), `entity_id`, `operation`, `duration`, `status`,
     `error_code` — mismos campos que pide observability (sección 25).
   - Verificar que ningún log imprime `Authorization`, tokens ni secretos
     (test explícito en Phase 0, ver `08_TEST_STRATEGY.md`).

9. **Sentry**
   - Inicializar Sentry SDK en `main.py` y en `workers/celery_app.py`,
     solo si `SENTRY_DSN` está seteado (no romper en local sin DSN).

10. **CI**
    - `.github/workflows/ci.yml`: en cada push/PR → `docker compose up -d
      postgres redis` → `make migrate` → `pytest` → `ruff`/`mypy` →
      `npm run lint` (web).
    - Sin despliegue automático todavía en Phase 0.

11. **Makefile**
    ```
    make up        # docker compose up -d
    make down
    make migrate   # alembic upgrade head
    make seed      # datos de ejemplo (1 usuario admin, sin fuentes reales)
    make test      # pytest + npm test
    make lint      # ruff + mypy + eslint
    ```

## Definición de "Phase 0 terminada"
- `docker compose up -d` levanta los 6 servicios sin error.
- `GET /health` y `GET /ready` responden 200.
- Login contra Supabase Auth funciona desde el frontend.
- Un log de prueba aparece en formato JSON estructurado, sin secretos.
- CI en verde con al menos 1 test real (no placeholder) por capa
  (backend unit, migration, frontend build).
- Ningún módulo de negocio (Sources, Content Queue, Render, Publisher)
  tiene código todavía — solo los modelos `users` y `system_settings`.

## Siguiente paso
Al terminar Phase 0: **parar y confirmar** antes de empezar Phase 1
(Content core), tal como exige la regla de trabajo del spec (sección 30).
