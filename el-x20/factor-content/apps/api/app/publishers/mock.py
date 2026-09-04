"""MockPublisherAdapter — usado en tests de scheduler_service/publish_worker
(spec 27: los tests de invariantes críticos corren contra el mock, nunca
contra las APIs reales en CI, ver docs/08_TEST_STRATEGY.md)."""
from app.publishers.base import PublishResult, PublisherAdapter, ValidationResult


class MockPublisherAdapter(PublisherAdapter):
    def __init__(self, *, fail_mode: str | None = None):
        """fail_mode: None | 'rate_limit' | 'token_expired' | 'network' | 'slow'
        — permite a los tests simular cada escenario sin tocar red real."""
        self.fail_mode = fail_mode

    def connect_account(self, auth_code: str) -> dict:
        return {"access_token": "mock-token", "refresh_token": "mock-refresh"}

    def refresh_credentials(self, credential_payload: dict) -> dict:
        if self.fail_mode == "token_expired":
            raise ConnectionError("token refresh falló (mock)")
        return {**credential_payload, "access_token": "mock-token-refreshed"}

    def get_account_info(self, credential_payload: dict) -> dict:
        return {"id": "mock-account-id", "username": "mock_user"}

    def validate_post(self, *, media_paths: list[str], caption: str, credential_payload: dict) -> ValidationResult:
        errors = []
        if len(caption) > 2200:
            errors.append("caption excede el máximo permitido")
        if not media_paths:
            errors.append("se requiere al menos un slide/media")
        return ValidationResult(valid=not errors, errors=errors)

    def publish_video(self, *, media_paths: list[str], caption: str, credential_payload: dict) -> PublishResult:
        if self.fail_mode == "rate_limit":
            raise RuntimeError("429 rate limited (mock)")
        if self.fail_mode == "network":
            raise ConnectionError("network error (mock)")
        if self.fail_mode == "token_expired":
            raise PermissionError("token expirado (mock)")
        return PublishResult(external_post_id="mock-post-123", status="published")

    def upload_draft(self, *, media_paths: list[str], caption: str, credential_payload: dict) -> PublishResult:
        return PublishResult(external_post_id="mock-draft-123", status="pending_manual_action")

    def get_post_status(self, *, external_post_id: str, credential_payload: dict) -> str:
        return "published"

    def get_post_metrics(self, *, external_post_id: str, credential_payload: dict) -> dict:
        return {"views": 0, "likes": 0, "comments": 0, "shares": 0}

    def disconnect_account(self, credential_payload: dict) -> None:
        pass
