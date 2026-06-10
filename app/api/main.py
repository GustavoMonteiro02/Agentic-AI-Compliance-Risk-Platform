from fastapi import FastAPI

from app.api.routes import (
    audit,
    assessments,
    demo,
    evaluation,
    evidence,
    reports,
    requirements,
    reviews,
    risk_register,
    runtime,
    systems,
)
from app.config import get_settings
from app.database.session import init_db


def create_app() -> FastAPI:
    settings = get_settings()
    init_db()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Agentic AI governance, compliance, risk, and audit-readiness platform.",
    )

    @app.on_event("startup")
    def on_startup() -> None:
        init_db()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name, "kind": "liveness"}

    app.include_router(systems.router)
    app.include_router(demo.router)
    app.include_router(assessments.router)
    app.include_router(evidence.router)
    app.include_router(reviews.router)
    app.include_router(audit.router)
    app.include_router(risk_register.router)
    app.include_router(reports.router)
    app.include_router(requirements.router)
    app.include_router(runtime.router)
    app.include_router(evaluation.router)
    return app


app = create_app()
