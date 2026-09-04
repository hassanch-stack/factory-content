# Factor Content

Content Operating System interno para gestionar publicación de FOTOS con
guion editorial reescrito por IA, en TikTok, Instagram y Facebook a escala
(5 cuentas / 25 piezas-día en V1), respetando siempre los derechos del
contenido y las reglas oficiales de cada plataforma.

> Nota: el producto pivotó de vídeo a foto — ver `docs/adr/0007-photo-pivot.md`.

Este repositorio contiene, de momento, **solo la fundación de Phase 0**:
arquitectura, decisiones de diseño y entorno de desarrollo. No hay código
de negocio todavía (eso empieza en Phase 1, ver roadmap).

## Empezar aquí
1. Lee `docs/01_REPO_TREE.md` — estructura del proyecto.
2. Lee `docs/02_adr/` — por qué se eligió cada pieza del stack.
3. Lee `docs/03_ERD.md` — modelo de datos.
4. Copia `infra/.env.example` a `infra/.env` y rellena los valores.
5. `docker compose -f infra/docker-compose.yml up -d`
6. Cuando exista el esqueleto de FastAPI/Alembic (Phase 0 en progreso):
   `make migrate && make seed && make test`

## Documentación
| Documento | Contenido |
|---|---|
| `docs/01_REPO_TREE.md` | Árbol de carpetas propuesto |
| `docs/adr/0001-...0006-...` | Architecture Decision Records |
| `docs/03_ERD.md` | Modelo de datos (Mermaid) + índices críticos |
| `docs/05_PHASE0_PLAN.md` | Plan de implementación de la fundación |
| `docs/06_SECURITY_CHECKLIST.md` | Seguridad y límites de la automatización |
| `docs/07_PLATFORM_INTEGRATION_CHECKLIST.md` | Qué validar antes de integrar cada plataforma |
| `docs/08_TEST_STRATEGY.md` | Estrategia de tests e invariantes críticos |

## Principios del producto
- No es primero un editor de vídeo — es un sistema de automatización de
  pipeline. El diferencial a largo plazo es: datos de fuentes + selección
  de contenido + velocidad de flujo + librería de templates + fiabilidad
  de publicación + datos propios de rendimiento + bucle de aprendizaje.
- La entrada de contenido en V1 es manual: el operador sube cada foto. No se
  consulta ni descarga contenido desde fuentes externas automáticamente.
- Nunca se elude una protección, límite o requisito oficial de plataforma.
- Toda publicación automática pasa por revisión humana salvo que se
  configure explícitamente lo contrario.

## Roadmap (fases)
`Phase 0` Fundación → `Phase 1` Content core → `Phase 2` Rendering →
`Phase 3` Review → `Phase 4` Scheduling → `Phase 5` Analytics →
`Phase 6` Intelligence (Factor Score, recomendaciones, A/B testing).

Cada fase se implementa, se testea y se confirma antes de pasar a la
siguiente (regla de trabajo, ver spec original sección 29-30).
