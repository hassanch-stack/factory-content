"""Logging estructurado en JSON. Redacta cualquier campo que parezca un
secreto — invariante de seguridad exigido por el spec (nunca credenciales
en logs) y cubierto por tests explícitos."""
import logging
from pythonjsonlogger import jsonlogger

_REDACT_KEYS = {"token", "secret", "password", "api_key", "authorization",
                "encrypted_payload", "client_secret", "access_key", "secret_key"}


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, "__dict__"):
            for key in list(record.__dict__.keys()):
                if key.lower() in _REDACT_KEYS:
                    record.__dict__[key] = "***REDACTED***"
        return True


def configure_logging(level: str = "info") -> None:
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s "
        "%(job_id)s %(entity_id)s %(operation)s %(duration)s %(status)s %(error_code)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
        defaults={"job_id": None, "entity_id": None, "operation": None,
                  "duration": None, "status": None, "error_code": None},
    )
    handler.setFormatter(formatter)
    handler.addFilter(RedactingFilter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
