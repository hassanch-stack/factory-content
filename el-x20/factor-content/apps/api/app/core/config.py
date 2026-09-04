"""Configuración central de la app. Todo valor sensible viene de env vars,
nunca hardcodeado (ver Security Checklist)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    log_level: str = "info"
    max_upload_size_bytes: int = 20 * 1024 * 1024
    auth_required: bool = False

    database_url: str
    redis_url: str

    s3_endpoint: str
    s3_bucket: str
    s3_access_key: str
    s3_secret_key: str
    s3_region: str = "auto"

    auth_secret: str
    encryption_key: str

    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None

    anthropic_api_key: str | None = None
    openai_api_key: str | None = None

    tiktok_client_key: str | None = None
    tiktok_client_secret: str | None = None
    tiktok_redirect_uri: str | None = None

    meta_app_id: str | None = None
    meta_app_secret: str | None = None
    meta_redirect_uri: str | None = None

    sentry_dsn: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
