# ADR 0005 — Storage S3-compatible (Cloudflare R2 preferido)

**Estado:** Aceptado

## Contexto
El spec prohíbe explícitamente guardar binarios de vídeo en PostgreSQL
(punto 6) y pide buckets/carpetas conceptuales: `originals/`, `working/`,
`rendered/`, `thumbnails/`, `subtitles/`, `exports/`, `temp/`.

## Decisión
Object storage compatible con la API S3, usando Cloudflare R2 como opción
preferida en producción; para desarrollo local, un contenedor
S3-compatible (ej. MinIO) en Docker Compose.

## Razones
- R2 no cobra egress (salida de datos), lo cual importa porque el flujo
  incluye subir a Instagram/TikTok/Facebook (lecturas repetidas del mismo
  archivo durante publish/retry) — con S3 estándar esas lecturas
  acumularían coste de egress.
- La API es S3-compatible, así que el cliente (`storage/s3_client.py`) no
  depende de un proveedor específico: cambiar a AWS S3, Backblaze B2 o
  MinIO on-prem es un cambio de configuración, no de código.
- URLs firmadas (signed URLs) cubren el requisito de seguridad del punto 24
  sin exponer el bucket públicamente.

## Alternativas consideradas
- **AWS S3**: viable, pero coste de egress más alto para el patrón de uso
  (múltiples reads del mismo vídeo al publicar/reintentar en 3 plataformas).
- **Guardar en disco local del servidor**: rechazado — no escala a
  múltiples workers, sin redundancia, complica backups.

## Consecuencias
- Requiere gestionar `S3_ENDPOINT`, `S3_BUCKET`, `S3_ACCESS_KEY`,
  `S3_SECRET_KEY`, `S3_REGION` como secretos (ver Security Checklist).
- La política de retención (punto 22, "cleanup") debe respetar el bucket
  `originals/` de forma más conservadora que `temp/`.
