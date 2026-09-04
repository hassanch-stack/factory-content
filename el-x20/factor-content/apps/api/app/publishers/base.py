"""Interfaz PublisherAdapter — spec sección 13 / ADR 0006. El scheduler
solo conoce esta interfaz, nunca una plataforma concreta. Cada adapter
real (TikTok/Instagram/Facebook) debe documentar en docs/adapters/*.md
sus límites vigentes ANTES de implementarse — nunca se asume."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PublishResult:
    external_post_id: str | None
    status: str  # "published" | "pending_manual_action" | "failed"
    raw_response: dict | None = None


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]


class PublisherAdapter(ABC):
    """Ninguna implementación de esta interfaz puede: simular actividad
    humana para evadir límites, eludir CAPTCHA/anti-bot, ni publicar sin
    pasar por el flujo oficial soportado (spec sección 2 — regla dura,
    sin excepción por plataforma)."""

    @abstractmethod
    def connect_account(self, auth_code: str) -> dict:
        """Completa el flujo OAuth y devuelve el payload a cifrar en
        PlatformCredential.encrypted_payload."""

    @abstractmethod
    def refresh_credentials(self, credential_payload: dict) -> dict:
        """Devuelve un payload de credenciales renovado."""

    @abstractmethod
    def get_account_info(self, credential_payload: dict) -> dict:
        ...

    @abstractmethod
    def validate_post(self, *, media_paths: list[str], caption: str, credential_payload: dict) -> ValidationResult:
        """Debe rechazar contenido que no cumpla requisitos de la
        plataforma ANTES de intentar publicar — nunca confiar en que la
        API remota hará esa validación por nosotros."""

    @abstractmethod
    def publish_video(self, *, media_paths: list[str], caption: str, credential_payload: dict) -> PublishResult:
        """A pesar del nombre heredado del spec original (vídeo), tras el
        pivote publica foto(s). media_paths es una lista porque el
        contenido puede ser un carrusel de varios slides (ej. hook + cuerpo
        con burbujas) en el mismo post — un solo elemento para post simple."""

    @abstractmethod
    def upload_draft(self, *, media_paths: list[str], caption: str, credential_payload: dict) -> PublishResult:
        """Fallback manual/user-driven cuando la publicación directa no
        está disponible (ej. TikTok sin app auditada)."""

    @abstractmethod
    def get_post_status(self, *, external_post_id: str, credential_payload: dict) -> str:
        ...

    @abstractmethod
    def get_post_metrics(self, *, external_post_id: str, credential_payload: dict) -> dict:
        ...

    @abstractmethod
    def disconnect_account(self, credential_payload: dict) -> None:
        ...
