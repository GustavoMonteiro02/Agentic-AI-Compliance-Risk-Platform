from app.config import get_settings


def langsmith_trace_metadata(assessment_id: str, workflow_name: str) -> dict:
    settings = get_settings()
    if not settings.langsmith_tracing:
        return {"enabled": False}
    return {
        "enabled": True,
        "project": settings.langsmith_project,
        "workflow": workflow_name,
        "trace_url": f"langsmith://{settings.langsmith_project}/{assessment_id}",
    }
