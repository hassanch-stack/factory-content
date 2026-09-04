"""FacebookAdapter — stub. Regla de trabajo del spec (sección 29): antes de
implementar contra la Graph API (Facebook) real hay que confirmar en la
documentación oficial vigente los items de
docs/07_PLATFORM_INTEGRATION_CHECKLIST.md (sección Facebook) — no se asume
nada aquí todavía.

Este adapter existe para que scheduler_service pueda instanciar por
platform="tiktok" sin romper, pero cada método real lanza
NotImplementedError hasta completar esa verificación."""
from app.publishers.base import PublishResult, PublisherAdapter, ValidationResult

_NOT_READY = (
    "FacebookAdapter no implementado: falta confirmar contra la documentación "
    "oficial vigente de la Graph API (Facebook) (ver "
    "docs/07_PLATFORM_INTEGRATION_CHECKLIST.md, sección Facebook) antes de "
    "escribir el código real."
)


class FacebookAdapter(PublisherAdapter):
    def connect_account(self, auth_code: str) -> dict:
        raise NotImplementedError(_NOT_READY)

    def refresh_credentials(self, credential_payload: dict) -> dict:
        raise NotImplementedError(_NOT_READY)

    def get_account_info(self, credential_payload: dict) -> dict:
        raise NotImplementedError(_NOT_READY)

    def validate_post(self, *, media_paths: list[str], caption: str, credential_payload: dict) -> ValidationResult:
        raise NotImplementedError(_NOT_READY)

    def publish_video(self, *, media_paths: list[str], caption: str, credential_payload: dict) -> PublishResult:
        raise NotImplementedError(_NOT_READY)

    def upload_draft(self, *, media_paths: list[str], caption: str, credential_payload: dict) -> PublishResult:
        raise NotImplementedError(_NOT_READY)

    def get_post_status(self, *, external_post_id: str, credential_payload: dict) -> str:
        raise NotImplementedError(_NOT_READY)

    def get_post_metrics(self, *, external_post_id: str, credential_payload: dict) -> dict:
        raise NotImplementedError(_NOT_READY)

    def disconnect_account(self, credential_payload: dict) -> None:
        raise NotImplementedError(_NOT_READY)
