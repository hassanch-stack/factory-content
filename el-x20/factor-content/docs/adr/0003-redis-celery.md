# ADR 0003 — Redis + Celery para colas, con interfaz abstracta

**Estado:** Aceptado

## Contexto
El sistema necesita 7 colas de trabajo (radar, import, render, ai, publish,
analytics, cleanup), cada job debe ser idempotente, con reintentos, timeout
y estado consultable (`RenderJob.status/progress`).

## Decisión
Redis como broker/backend, Celery como framework de tareas para V1. La
interfaz de encolado se abstrae detrás de un módulo `queue/` propio
(`enqueue_render_job()`, `enqueue_publish()`, etc.) en vez de llamar a
`celery.send_task` directamente desde `services/`.

## Razones
- Celery es la opción más madura en Python para colas con reintentos,
  retries con backoff exponencial, rate limiting por cola y `celery beat`
  para tareas periódicas (radar cada 1-5 min, analytics cada 15m/1h/6h/24h).
- Redis además sirve como cache ligero (ej. resultados de AI cacheados,
  punto 22 del spec: "never regenerate identical input unnecessarily").

## Alternativas consideradas
- **RQ (Redis Queue)**: más simple, pero sin beat/periodic tasks nativo tan
  robusto y sin retries configurables tan finos.
- **Cola nativa (Postgres `SKIP LOCKED`) sin Celery**: rechazado por menor
  ecosistema (retries, backoff, monitoring) para V1, aunque queda como
  opción de migración futura precisamente porque la interfaz de encolado
  está abstraída.

## Consecuencias
- Se puede sustituir Celery por otra cosa (RQ, Postgres-based, SQS) sin
  tocar `services/`, porque estos nunca importan Celery directamente.
- Requiere monitorizar profundidad de cola y "unbounded queue" (punto 21
  del spec: no permitir colas sin límite) desde el dashboard `/jobs`.
