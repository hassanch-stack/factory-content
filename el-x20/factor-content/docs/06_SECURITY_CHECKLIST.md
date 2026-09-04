# Security Checklist — Factor Content

Basado en la sección 24 del spec. Marcar cada ítem al implementarlo, no antes.

## Transporte y sesión
- [ ] HTTPS obligatorio en cualquier entorno que no sea `localhost`.
- [ ] Cookies de sesión: `Secure`, `HttpOnly`, `SameSite=Lax` (o `Strict` si
      el flujo de auth lo permite).
- [ ] CSRF protection en endpoints que mutan estado y se llaman desde el
      navegador con cookies (no necesario si el frontend usa Bearer token
      en header, pero decidir explícitamente uno de los dos modelos).

## Secretos y credenciales
- [ ] Ningún secreto (`TIKTOK_CLIENT_SECRET`, `META_APP_SECRET`,
      `ENCRYPTION_KEY`, `S3_SECRET_KEY`, etc.) en columnas de BD sin cifrar.
      `platform_credentials.encrypted_payload` se cifra con `ENCRYPTION_KEY`
      antes de persistir.
- [ ] `.env` nunca commiteado (verificado en `.gitignore` + pre-commit hook
      opcional que bloquea si detecta patrones tipo `sk-`, `Bearer `, etc.).
- [ ] Rotación de secretos documentada: qué hacer si `TIKTOK_CLIENT_SECRET`
      se compromete (revocar en la plataforma, regenerar, redeploy).
- [ ] Ningún secreto en el bundle de frontend (`NEXT_PUBLIC_*` solo para
      valores no sensibles, ej. `NEXT_PUBLIC_API_URL`).

## Logs
- [ ] Ningún log imprime tokens, `Authorization` header, contraseñas ni
      `encrypted_payload` desencriptado.
- [ ] Test automático (`08_TEST_STRATEGY.md`) que falla si un logger recibe
      una clave sospechosa (`token`, `secret`, `password`, `api_key`) sin
      redactar.

## Autorización
- [ ] Toda autorización se valida server-side (FastAPI dependency), nunca
      confiando en el estado del frontend.
- [ ] Los endpoints de `publishers/*` verifican que la cuenta pertenece al
      usuario/tenant antes de usar sus credenciales.

## Auditoría
- [ ] Tabla `audit_logs` registra: quién, qué acción, sobre qué entidad,
      estado antes/después, cuándo — para acciones sensibles (aprobar/
      rechazar contenido, publicar, cambiar credenciales, borrar fuente).

## Uploads y media
- [ ] Validación de tipo MIME real (no solo extensión) en cualquier subida.
- [ ] Límite de tamaño de archivo configurable, rechazado con error claro
      si se excede.
- [ ] Protección contra path traversal al construir `storage_key` (nunca
      usar el nombre de archivo del usuario/fuente directamente como key).
- [ ] URLs de descarga/lectura del bucket son firmadas y con expiración,
      nunca objetos públicos por defecto.

## Alcance de la automatización (cumplimiento explícito del spec, secc. 2)
- [ ] No existe código de: harvesting de credenciales de terceros, bypass
      de CAPTCHA, bypass de anti-bot, bypass de rate limits de plataforma,
      elusión de DRM, scraping de contenido privado, eliminación de
      watermark para ocultar origen, generación de engagement falso,
      creación automatizada de cuentas, o publicación tipo spam.
- [ ] Toda fuente con `permission_status = UNKNOWN` requiere aprobación
      explícita del operador antes de que el Radar la procese
      automáticamente (regla dura del punto 5.1 del spec).
- [ ] Contenido sin `rights_status` aceptable no puede entrar al flujo de
      publicación automática (invariante también cubierta en tests).

## Infraestructura
- [ ] Backups automáticos de PostgreSQL con retención definida.
- [ ] `docker-compose.override.yml.example` documenta cómo NO exponer
      puertos de `postgres`/`redis`/`minio` directamente a internet en
      producción.
