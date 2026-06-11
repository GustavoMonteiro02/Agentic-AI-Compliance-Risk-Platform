from datetime import datetime
from typing import Any

import requests

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


def build_langsmith_experiment_payload(results: list[dict[str, Any]], experiment_name: str) -> dict[str, Any]:
    settings = get_settings()
    return {
        "project": settings.langsmith_project,
        "experiment_name": experiment_name,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "source": "ai-governance-compliance-platform",
        "summary": {
            "metric_count": len(results),
            "average_score": round(sum(float(item.get("score", 0.0)) for item in results) / len(results), 3)
            if results
            else 0.0,
            "passing": all(float(item.get("score", 0.0)) >= 0.75 for item in results),
        },
        "runs": [
            {
                "name": item["metric_name"],
                "inputs": {"metric_name": item["metric_name"]},
                "outputs": {"score": item.get("score"), "details": item.get("details", {})},
                "metadata": {
                    "project": settings.langsmith_project,
                    "evaluation_type": "offline_regression",
                },
            }
            for item in results
        ],
    }


def upload_langsmith_experiment(payload: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    if not settings.langsmith_api_key:
        return {"uploaded": False, "reason": "missing_langsmith_api_key", "payload": payload}

    response = requests.post(
        f"{settings.langsmith_api_url.rstrip('/')}/runs/batch",
        headers={
            "x-api-key": settings.langsmith_api_key,
            "Content-Type": "application/json",
        },
        json={"post": payload["runs"]},
        timeout=30,
    )
    response.raise_for_status()
    return {
        "uploaded": True,
        "project": payload["project"],
        "experiment_name": payload["experiment_name"],
        "run_count": len(payload["runs"]),
        "response": response.json() if response.content else {},
    }
