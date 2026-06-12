import py_compile
import json
from pathlib import Path


def test_streamlit_app_compiles():
    py_compile.compile(str(Path("frontend/streamlit_app.py")), doraise=True)


def test_react_saas_ui_scaffold_is_present():
    package = json.loads(Path("frontend/react_app/package.json").read_text(encoding="utf-8"))
    app = Path("frontend/react_app/src/App.tsx").read_text(encoding="utf-8")
    styles = Path("frontend/react_app/src/styles.css").read_text(encoding="utf-8")

    assert package["scripts"]["dev"].startswith("vite")
    assert "lucide-react" in package["dependencies"]
    assert "Governance command center" in app
    assert "Open incidents" in app
    assert "Escalated reviews" in app
    assert "Runtime readiness" in app
    assert "Legal source readiness" in app
    assert "API latency" in app
    assert "Evidence approved" in app
    assert 'getJson<RuntimeMetrics>("/runtime/metrics")' in Path(
        "frontend/react_app/src/api.ts"
    ).read_text(encoding="utf-8")
    assert 'getJson<RuntimeReadiness>("/runtime/readiness")' in Path(
        "frontend/react_app/src/api.ts"
    ).read_text(encoding="utf-8")
    assert 'getJson<Incident[]>("/incidents")' in Path("frontend/react_app/src/api.ts").read_text(encoding="utf-8")
    assert 'getJson<ReviewEscalation[]>("/reviews/escalations")' in Path(
        "frontend/react_app/src/api.ts"
    ).read_text(encoding="utf-8")
    assert 'getJson<LegalSourceSummary>("/requirements/legal-sources")' in Path(
        "frontend/react_app/src/api.ts"
    ).read_text(encoding="utf-8")
    assert "grid-template-columns: 280px minmax(0, 1fr)" in styles
    assert "@media (max-width: 1120px)" in styles
    assert "overflow-x: auto" in styles


def test_github_actions_builds_react_command_center():
    workflow = Path(".github/workflows/tests.yml").read_text(encoding="utf-8")

    assert "actions/setup-node@v4" in workflow
    assert "working-directory: frontend/react_app" in workflow
    assert "npm install" in workflow
    assert "npm run build" in workflow
