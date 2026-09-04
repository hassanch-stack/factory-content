"""Guardia de acceso para el operador interno."""
from __future__ import annotations

import secrets

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import Settings

PUBLIC_PATHS = {"/health", "/ready", "/docs", "/openapi.json", "/redoc"}


async def enforce_operator_auth(request: Request, call_next, *, settings: Settings):
    """Exige AUTH_SECRET como Bearer token cuando AUTH_REQUIRED está activo.

    V1 es una herramienta de un solo operador. El token nunca se escribe en
    logs ni se acepta por query string.
    """
    if not settings.auth_required or request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token or not secrets.compare_digest(token, settings.auth_secret):
        return JSONResponse(status_code=401, content={"detail": "Autenticación de operador requerida."})
    return await call_next(request)
