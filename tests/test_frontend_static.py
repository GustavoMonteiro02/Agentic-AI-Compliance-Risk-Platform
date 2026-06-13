import json
from pathlib import Path


def test_react_saas_ui_scaffold_is_present():
    package = json.loads(Path("frontend/react_app/package.json").read_text(encoding="utf-8"))
    app = Path("frontend/react_app/src/App.tsx").read_text(encoding="utf-8")
    styles = Path("frontend/react_app/src/styles.css").read_text(encoding="utf-8")

    assert package["scripts"]["dev"].startswith("vite")
    assert "lucide-react" in package["dependencies"]
    assert "Enterprise AI risk platform" in app
    assert "Create and assess" in app
    assert "Traceability map" in app
    assert "Requirements search" in app
    assert "Evidence center" in app
    assert "Risk register" in app
    assert "Incident response" in app
    assert "Human review" in app
    assert "LLM usage" in app
    assert "Configured LLMs" in app
    assert "Runtime readiness" in app
    assert "Governance support, not legal advice." in app
    api = Path("frontend/react_app/src/api.ts").read_text(encoding="utf-8")
    assert 'request<RuntimeMetrics>("GET", "/runtime/metrics")' in api
    assert 'request<LLMOptions>("GET", "/runtime/llm-options")' in api
    assert 'request<SystemRecord>("POST", "/systems", payload)' in api
    assert 'request<Assessment>("POST", `/systems/${systemId}/assess`, payload)' in api
    assert 'request<EvidenceRecord>("PATCH", `/evidence/items/${evidenceId}`, payload)' in api
    assert 'request<Incident>("POST", "/incidents", payload)' in api
    assert 'request<Record<string, unknown>>("POST", `/reviews/${assessmentId}/${action}`, payload)' in api
    assert "grid-template-columns: 270px minmax(0, 1fr)" in styles
    assert "@media (max-width: 1180px)" in styles
    assert "overflow-x: auto" in styles


def test_github_actions_builds_react_command_center():
    workflow = Path(".github/workflows/tests.yml").read_text(encoding="utf-8")

    assert "actions/setup-node@v4" in workflow
    assert "working-directory: frontend/react_app" in workflow
    assert "npm install" in workflow
    assert "npm run build" in workflow
