# Factor Content — Repository Tree (Phase 0)

Modular monolith + workers, monorepo. Un solo repo, dos "apps" (web/api) y un
paquete de workers que reutiliza el código del API (misma base, sin duplicar lógica).

```
factor-content/
├── apps/
│   ├── web/                         # Next.js (dashboard operador)
│   │   ├── app/
│   │   │   ├── dashboard/
│   │   │   ├── radar/
│   │   │   ├── queue/
│   │   │   ├── editor/
│   │   │   ├── review/
│   │   │   ├── calendar/
│   │   │   ├── accounts/
│   │   │   ├── sources/
│   │   │   ├── templates/
│   │   │   ├── analytics/
│   │   │   ├── settings/
│   │   │   └── jobs/
│   │   ├── components/
│   │   ├── lib/                     # cliente API tipado (OpenAPI-generated)
│   │   ├── public/
│   │   ├── package.json
│   │   └── tailwind.config.ts
│   │
│   └── api/                         # FastAPI
│       ├── app/
│       │   ├── main.py
│       │   ├── core/
│       │   │   ├── config.py        # settings (pydantic-settings)
│       │   │   ├── security.py      # auth, secretos, cifrado
│       │   │   ├── logging.py       # logs estructurados
│       │   │   └── db.py            # engine/session SQLAlchemy
│       │   ├── models/              # SQLAlchemy/SQLModel ORM
│       │   │   ├── source.py
│       │   │   ├── content_item.py
│       │   │   ├── media_asset.py
│       │   │   ├── template.py
│       │   │   ├── render_job.py
│       │   │   ├── ai_generation.py
│       │   │   ├── account.py
│       │   │   ├── post.py
│       │   │   ├── post_metrics.py
│       │   │   ├── platform_credential.py
│       │   │   └── audit_log.py
│       │   ├── schemas/             # Pydantic (request/response)
│       │   ├── routers/             # /api/* route groups
│       │   │   ├── auth.py
│       │   │   ├── sources.py
│       │   │   ├── radar.py
│       │   │   ├── content.py
│       │   │   ├── media.py
│       │   │   ├── templates.py
│       │   │   ├── render.py
│       │   │   ├── review.py
│       │   │   ├── accounts.py
│       │   │   ├── schedules.py
│       │   │   ├── posts.py
│       │   │   ├── analytics.py
│       │   │   ├── ai.py
│       │   │   ├── system.py
│       │   │   └── webhooks.py
│       │   ├── services/            # lógica de negocio (no en routers)
│       │   │   ├── radar_service.py
│       │   │   ├── dedup_service.py
│       │   │   ├── scoring_service.py     # Factor Score
│       │   │   ├── render_service.py
│       │   │   ├── ai_service.py
│       │   │   ├── scheduler_service.py
│       │   │   └── analytics_service.py
│       │   ├── publishers/          # Publisher abstraction + adapters
│       │   │   ├── base.py          # interfaz PublisherAdapter
│       │   │   ├── tiktok.py
│       │   │   ├── instagram.py
│       │   │   └── facebook.py
│       │   ├── media/
│       │   │   ├── ffmpeg_runner.py
│       │   │   └── template_engine.py
│       │   ├── storage/
│       │   │   └── s3_client.py     # Cloudflare R2 / S3-compatible
│       │   └── queue/
│       │       └── celery_app.py
│       ├── alembic/
│       │   ├── versions/
│       │   └── env.py
│       ├── tests/
│       │   ├── unit/
│       │   ├── integration/
│       │   └── e2e/
│       ├── pyproject.toml
│       └── Dockerfile
│
├── workers/                         # entrypoints Celery (importan apps/api/app)
│   ├── radar_worker.py
│   ├── import_worker.py
│   ├── render_worker.py
│   ├── ai_worker.py
│   ├── publish_worker.py
│   ├── analytics_worker.py
│   ├── cleanup_worker.py
│   ├── beat_schedule.py             # celery beat: radar/analytics periódicos
│   └── Dockerfile
│
├── docs/
│   ├── 01_REPO_TREE.md
│   ├── 02_ADRs/
│   ├── 03_ERD.md
│   ├── 04_ENV_VARS.md
│   ├── 05_PHASE0_PLAN.md
│   ├── 06_SECURITY_CHECKLIST.md
│   ├── 07_PLATFORM_INTEGRATION_CHECKLIST.md
│   ├── 08_TEST_STRATEGY.md
│   └── adapters/                    # doc por plataforma (scopes, límites, retries)
│       ├── tiktok.md
│       ├── instagram.md
│       └── facebook.md
│
├── infra/
│   ├── docker-compose.yml
│   ├── docker-compose.override.yml.example
│   └── .env.example
│
├── Makefile
├── .github/workflows/ci.yml
├── .gitignore
└── README.md
```

## Convenciones
- Monorepo, pero **no microservicios**: `apps/api` es el único proceso "servidor";
  `workers/` son procesos Celery que importan directamente `apps/api/app`, así no se
  duplica lógica de modelos/servicios.
- Todo el código con reglas de negocio vive en `services/`, nunca en los routers.
- Los adapters de plataforma nunca se referencian directamente desde `scheduler_service.py`;
  siempre a través de la interfaz `PublisherAdapter`.
