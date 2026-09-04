# ADR 0002 — PostgreSQL como base de datos primaria

**Estado:** Aceptado

## Contexto
Factor Content necesita: relaciones fuertes (source → content_item → media_asset
→ render_job → post → post_metrics), transacciones (aprobar/rechazar contenido,
publicar sin duplicados), JSON semi-estructurado (metadata de plataforma,
configuración de templates) e índices compuestos para consultas de scheduler
y analítica.

## Decisión
PostgreSQL, con SQLAlchemy/SQLModel + Alembic para migraciones.

## Razones
- Soporta columnas `JSONB` para `metadata_json`, `configuration_json` y
  métricas específicas de plataforma sin perder capacidad relacional.
- Índices parciales/compuestos para las consultas críticas del scheduler
  (`posts(status, scheduled_at)`) y del dashboard.
- `SELECT ... FOR UPDATE SKIP LOCKED` (o equivalente) permite implementar el
  locking que exige el punto 15 del spec ("dos workers no pueden publicar el
  mismo post") sin infraestructura adicional.
- Ecosistema maduro de migraciones (Alembic) y de backups.

## Alternativas consideradas
- **MongoDB**: rechazado — el dominio es fuertemente relacional (estado de
  contenido, jobs, posts, métricas), y el spec exige invariantes tipo "un
  post no puede publicarse dos veces", que se modelan mejor con constraints
  relacionales.
- **MySQL**: viable, pero PostgreSQL tiene mejor soporte de JSONB e índices
  parciales, útiles para el `Factor Score` y las consultas de analítica.

## Consecuencias
- Un único punto de verdad para el estado de todo el pipeline.
- Requiere backups/point-in-time-recovery desde el día 1 (ver Security
  Checklist).
