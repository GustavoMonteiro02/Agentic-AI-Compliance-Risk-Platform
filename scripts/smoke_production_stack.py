from pathlib import Path
import os
import sys
import time

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
PLATFORM_API_KEY = os.getenv("PLATFORM_API_KEY")
TENANT_ID = os.getenv("PLATFORM_TENANT_ID", os.getenv("DEFAULT_TENANT_ID", "prod-test"))


def headers(role: str = "admin") -> dict[str, str]:
    values = {
        "X-User": "production-smoke",
        "X-User-Role": role,
        "X-Tenant-ID": TENANT_ID,
    }
    if PLATFORM_API_KEY:
        values["X-API-Key"] = PLATFORM_API_KEY
    return values


def request(method: str, path: str, *, role: str = "admin", json: dict | None = None) -> requests.Response:
    response = requests.request(
        method,
        f"{API_BASE_URL}{path}",
        headers=headers(role),
        json=json,
        timeout=120,
    )
    response.raise_for_status()
    return response


def wait_for_api() -> None:
    for _ in range(30):
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                return
        except requests.RequestException:
            time.sleep(2)
    raise RuntimeError(f"API did not become ready at {API_BASE_URL}")


def main() -> int:
    wait_for_api()

    status = request("GET", "/runtime/status").json()
    preflight = request("GET", "/runtime/preflight?target=production").json()
    print({"llm_enabled": status["llm_enabled"], "vector_db": status["vector_db"], "auth_mode": status["auth_mode"]})
    print({"release_ready": preflight["release_ready"], "warnings": preflight["warning_count"], "blockers": preflight["blocker_count"]})

    system = request(
        "POST",
        "/systems",
        json={
            "name": "Production Smoke HR Assistant",
            "description": (
                "AI assistant in HR analyzes CVs, ranks candidates, stores embeddings, "
                "and produces recommendations for recruiters. Human reviewers make final decisions."
            ),
            "business_unit": "People Operations",
            "owner": "Compliance",
            "technical_owner": "AI Engineering",
            "deployment_status": "production",
            "data_types": ["CV", "candidate profile", "email"],
            "model_provider": "OpenAI",
            "model_type": "LLM workflow",
            "decision_impact": "employment",
            "autonomy_level": "human_in_the_loop",
            "human_oversight_process": "Recruiters approve all candidate decisions.",
            "metadata": {
                "external_users_affected": False,
                "monitoring_status": "active",
                "evaluation_status": "scheduled",
                "security_testing_status": "planned",
            },
        },
    ).json()
    assessment = request("POST", f"/systems/{system['id']}/assess").json()
    usage = request("GET", f"/assessments/{assessment['id']}/llm-usage", role="auditor").json()
    rag = request(
        "GET",
        "/requirements/search?q=AI%20Act%20human%20oversight%20employment%20personal%20data&top_k=3",
        role="auditor",
    ).json()

    print(
        {
            "assessment_id": assessment["id"],
            "risk_level": assessment["risk_classification"]["risk_level"],
            "llm_calls": usage["llm_call_count"],
            "total_tokens": usage["total_tokens"],
            "top_requirement": rag[0]["title"] if rag else None,
        }
    )
    if status["ai_generation_mode"] in {"openai", "llm"} and usage["llm_call_count"] == 0:
        raise RuntimeError("LLM mode is enabled but no LLM calls were recorded for the assessment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
