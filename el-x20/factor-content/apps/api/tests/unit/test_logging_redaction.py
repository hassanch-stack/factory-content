"""Invariante crítico: las credenciales nunca aparecen en logs (spec 24/27)."""
import io
import json
import logging

from app.core.logging import configure_logging


def test_secret_fields_are_redacted(capsys):
    configure_logging("info")
    logger = logging.getLogger("test")

    logger.info("evento sensible", extra={"job_id": "abc", "api_key": "sk-real-secret-value"})

    captured = capsys.readouterr()
    assert "sk-real-secret-value" not in captured.err
