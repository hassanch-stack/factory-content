# ADR 0001 — Modular Monolith + Workers (no microservicios)

**Estado:** Aceptado
**Fecha:** V1

## Contexto
Factor Content es una plataforma interna (un operador, 5 cuentas, ~750
vídeos/mes en V1). No hay requisito de multi-tenant público ni de escalar
equipos de ingeniería independientes por servicio.

## Decisión
Un único backend FastAPI (modular monolith) organizado en `routers/` (HTTP),
`services/` (lógica de negocio) y `publishers/` (adapters de plataforma),
más un conjunto de **workers Celery** que importan directamente ese mismo
código para ejecutar trabajo asíncrono (radar, import, render, ai, publish,
analytics, cleanup).

## Alternativas consideradas
- **Microservicios por dominio** (radar-service, render-service, publish-service...):
  rechazado en V1. Añade complejidad operativa (service discovery, contratos
  entre servicios, despliegue múltiple) que no aporta valor con un solo
  operador y volumen moderado.
- **Serverless (Lambda-style) para render**: rechazado por FFmpeg — trabajos
  de render pueden ser largos y con estado (progreso), encajan mejor en
  workers de larga duración con colas.

## Consecuencias
- Positivas: despliegue simple (Docker Compose → 1 imagen API + 1 imagen
  workers), debugging más fácil, cambios cross-cutting (ej. cambiar el
  modelo `ContentItem`) no requieren coordinar varios repos/servicios.
- Negativas: si el proyecto escala a multi-tenant público o a un equipo
  grande, en algún punto puede requerir separar `publishers/` o `render/`
  en servicios propios. Se documenta como deuda técnica aceptada, no como
  bloqueo — la separación en módulos internos (`services/`, `publishers/`)
  ya deja preparada esa futura extracción.
