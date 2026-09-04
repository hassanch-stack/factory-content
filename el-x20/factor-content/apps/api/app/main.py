from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.auth import enforce_operator_auth
from app.core.logging import configure_logging
from app.routers import (
    accounts,
    ai,
    analytics,
    content,
    intelligence,
    posts,
    render,
    review,
    schedules,
    script_templates,
    sources,
    system,
    templates,
)

settings = get_settings()
configure_logging(settings.log_level)

if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.environment)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Factor Content API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def operator_auth_middleware(request, call_next):
    return await enforce_operator_auth(request, call_next, settings=settings)

app.include_router(system.router)
app.include_router(sources.router)
app.include_router(content.router)
app.include_router(templates.router)
app.include_router(script_templates.router)
app.include_router(render.router)
app.include_router(ai.router)
app.include_router(review.router)
app.include_router(accounts.router)
app.include_router(schedules.router)
app.include_router(posts.router)
app.include_router(analytics.router)
app.include_router(intelligence.router)
