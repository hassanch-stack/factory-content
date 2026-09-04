# ADR 0006 — Publisher Adapter (interfaz abstracta por plataforma)

**Estado:** Aceptado

## Contexto
TikTok, Instagram y Facebook tienen APIs, scopes, límites de tasa y flujos
de autorización distintos entre sí. El spec exige explícitamente (punto 13):
"Never hard-code one platform's behavior into the generic scheduler" y
soportar un **fallback manual/user-driven** cuando la publicación directa
por API no esté disponible (relevante sobre todo para TikTok, cuyo Direct
Post API requiere app aprobada y scopes autorizados).

## Decisión
Interfaz `PublisherAdapter` con métodos: `connect_account`,
`refresh_credentials`, `get_account_info`, `validate_post`,
`publish_video`, `upload_draft`, `get_post_status`, `get_post_metrics`,
`disconnect_account`. Tres implementaciones: `TikTokAdapter`,
`InstagramAdapter`, `FacebookAdapter`. El `scheduler_service` solo conoce
la interfaz, nunca una plataforma concreta.

Cada adapter debe declarar en `docs/adapters/<plataforma>.md`:
operaciones soportadas, scopes requeridos, límites de tasa, restricciones
conocidas, reglas de reintento y features no soportadas — **basado en la
documentación oficial vigente de cada plataforma**, no en supuestos.

## Razones
- Permite añadir una cuarta plataforma sin tocar el scheduler.
- El fallback manual (`upload_draft` / "unaudited clients restricted to
  private viewing" en TikTok) se modela como un estado legítimo del Post
  (`MANUAL_ACTION_REQUIRED`), no como un error a ocultar.
- Cumple el requisito explícito del spec de no construir bypass de
  restricciones de plataforma: la interfaz solo expone operaciones
  soportadas oficialmente.

## Alternativas consideradas
- **Un único cliente genérico "social media API"**: rechazado — las
  diferencias reales entre TikTok/Instagram/Facebook (auth, formatos,
  límites) son demasiado grandes para abstraerlas sin perder control de
  errores específicos de cada una.

## Consecuencias
- Antes de implementar cada adapter, es obligatorio (regla de trabajo del
  spec, punto 29): parar y consultar la documentación oficial vigente si
  hay incertidumbre sobre requisitos de la API, en vez de asumir.
- Los tests de scheduler pueden usar un `MockPublisherAdapter`, sin
  necesidad de credenciales reales de ninguna plataforma.
