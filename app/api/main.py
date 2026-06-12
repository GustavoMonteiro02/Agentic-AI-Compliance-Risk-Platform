from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import (
    audit,
    assessments,
    demo,
    evaluation,
    evidence,
    incidents,
    reports,
    requirements,
    reviews,
    risk_register,
    runtime,
    systems,
)
from app.api.errors import http_exception_handler, validation_exception_handler
from app.config import get_settings
from app.database.session import init_db
from app.security.middleware import (
    HTTPMetricsMiddleware,
    InMemoryRateLimitMiddleware,
    RequestIDMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
)


def create_app() -> FastAPI:
    settings = get_settings()
    init_db()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_db()
        yield

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Agentic AI governance, compliance, risk, and audit-readiness platform.",
        lifespan=lifespan,
    )
    if settings.api_rate_limit_per_minute > 0:
        app.add_middleware(InMemoryRateLimitMiddleware, requests_per_minute=settings.api_rate_limit_per_minute)
    if settings.max_request_body_bytes > 0:
        app.add_middleware(RequestSizeLimitMiddleware, max_body_bytes=settings.max_request_body_bytes)
    if settings.security_headers_enabled:
        app.add_middleware(SecurityHeadersMiddleware, hsts_enabled=settings.security_hsts_enabled)
    app.add_middleware(HTTPMetricsMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-User", "X-User-Role", "X-Tenant-ID"],
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name, "kind": "liveness"}

    app.include_router(systems.router)
    app.include_router(demo.router)
    app.include_router(assessments.router)
    app.include_router(evidence.router)
    app.include_router(reviews.router)
    app.include_router(audit.router)
    app.include_router(incidents.router)
    app.include_router(risk_register.router)
    app.include_router(reports.router)
    app.include_router(requirements.router)
    app.include_router(runtime.router)
    app.include_router(evaluation.router)
    return app


app = create_app()
