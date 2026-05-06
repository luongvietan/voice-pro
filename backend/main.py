"""FastAPI entry — `uvicorn main:app` từ thư mục backend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.users import router as users_router
from app.config import get_settings
from app.middleware.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            integrations=[FastApiIntegration()],
            traces_sample_rate=0.1,
        )

    application = FastAPI(
        title="Voice-Pro API",
        version="0.1.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_origin_regex=r"chrome-extension://[\w-]+",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RateLimitMiddleware)

    application.include_router(health_router, tags=["health"])
    application.include_router(auth_router, prefix="/api/v1", tags=["auth"])
    application.include_router(users_router, prefix="/api/v1", tags=["users"])
    application.include_router(jobs_router, prefix="/api/v1")

    return application


app = create_app()
