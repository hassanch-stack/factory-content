# Platform Integration Checklist — Factor Content

Regla de trabajo (spec, sección 29): si hay incertidumbre sobre un requisito
de API externa, **parar y consultar la documentación oficial vigente**, no
asumir. Esta checklist se actualiza con lo que confirme esa consulta, no se
rellena por adelantado con supuestos.

## Antes de implementar cualquier adapter (aplica a las 3 plataformas)
- [ ] Confirmar en la documentación oficial actual: scopes exactos
      necesarios, límites de tasa vigentes, formatos de vídeo/duración
      soportados, y política de uso de datos/contenido.
- [ ] Documentar el resultado en `docs/adapters/<plataforma>.md` con fecha
      de consulta (las políticas de estas APIs cambian con frecuencia).
- [ ] Confirmar el flujo de auth completo (OAuth) en un entorno de prueba
      antes de integrarlo al scheduler.
- [ ] Definir explícitamente qué pasa cuando el token expira a mitad de un
      job de publicación (reintento tras refresh vs. `MANUAL_ACTION_REQUIRED`).

## TikTok — Content Posting API
- [ ] Confirmar estado de la app: auditada vs. no auditada (afecta si el
      contenido publicado es público o queda restringido a "solo yo").
- [ ] Confirmar si se usa Direct Post o el flujo de Draft/Inbox (upload y
      el usuario completa la publicación desde la app de TikTok).
- [ ] Implementar `creator_info` retrieval antes de intentar publicar (la
      API lo requiere para validar límites de la cuenta).
- [ ] Implementar polling de `publish_status` en vez de asumir éxito
      inmediato tras el `POST` de publicación.
- [ ] Documentar límites de tasa vigentes y cómo el `publish_worker` los
      respeta (backoff, no reintento agresivo).
- [ ] Documentar qué campos de disclosure de contenido (branded content /
      AI-generated, si aplica) deben marcarse — relevante porque parte del
      contenido pasa por `ai_generations`.

## Instagram — Graph API
- [ ] Confirmar tipo de cuenta requerida (Business/Creator vinculada a
      página de Facebook) como prerequisito de publicación por API.
- [ ] Confirmar formatos soportados para Reels vía API (duración, aspect
      ratio, tamaño de archivo).
- [ ] Confirmar límites de publicaciones por cuenta/día vigentes.
- [ ] Definir manejo de contenedores de media (creación de contenedor →
      publicación) como dos pasos en `publish_video`, si la API lo requiere.

## Facebook — Graph API
- [ ] Confirmar página vinculada y permisos (`pages_manage_posts` u
      homólogo vigente) necesarios.
- [ ] Confirmar si el formato de vídeo corto (Reels de Facebook) usa el
      mismo endpoint que Instagram o uno separado.
- [ ] Confirmar límites de tasa vigentes, específicos de esta API.

## Transversal — App Review / aprobación
- [ ] Registrar el proceso y tiempos estimados de aprobación de cada app
      (TikTok Content Posting API y Meta Graph API suelen requerir review).
- [ ] Mientras una app no esté aprobada: el fallback manual/draft debe
      estar disponible y probado — Factor Content **no puede depender**
      de que la aprobación llegue a tiempo para operar en V1.
- [ ] Confirmar requisitos de política de datos de usuario (qué se puede
      almacenar de `post_metrics`, cuánto tiempo, y si aplica algún
      requisito de eliminación bajo solicitud).

## No hacer (recordatorio explícito del spec)
- No diseñar ningún adapter asumiendo evasión de límites de tasa,
  automatización de sesiones de navegador simulando actividad humana, o
  publicación sin pasar por los flujos oficiales soportados.
