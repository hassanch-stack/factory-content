FROM python:3.11-slim

# libjpeg/zlib para Pillow (composición de fotos); ya no se necesita ffmpeg
# tras el pivote vídeo->foto.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl libjpeg62-turbo zlib1g \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY apps/api/pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir -e ".[dev]" 2>/dev/null || pip install --no-cache-dir \
    fastapi uvicorn[standard] pydantic pydantic-settings sqlalchemy "psycopg[binary]" \
    alembic celery redis boto3 "sentry-sdk[fastapi]" python-json-logger httpx Pillow anthropic
RUN pip install --no-cache-dir python-multipart

COPY apps/api /app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
