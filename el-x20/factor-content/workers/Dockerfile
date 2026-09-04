FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo zlib1g \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /
COPY apps/api/pyproject.toml /tmp/pyproject.toml
RUN pip install --no-cache-dir \
    fastapi pydantic pydantic-settings sqlalchemy "psycopg[binary]" \
    alembic celery redis boto3 "sentry-sdk[fastapi]" python-json-logger httpx Pillow anthropic python-multipart

COPY apps/api/app /app
COPY workers /workers

ENV PYTHONPATH=/:/app
CMD ["celery", "-A", "workers.celery_app", "worker", "--loglevel=info"]
