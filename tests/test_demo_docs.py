from pathlib import Path


def test_demo_assets_exist_for_portfolio_readme():
    for path in [
        Path("docs/assets/dashboard.png"),
        Path("docs/assets/risk-assessment.png"),
        Path("docs/assets/evidence-center.png"),
        Path("docs/assets/demo-flow.gif"),
    ]:
        assert path.exists()
        assert path.stat().st_size > 1000


def test_demo_guide_references_walkthrough():
    text = Path("docs/DEMO.md").read_text(encoding="utf-8")

    assert "Demo Scenarios" in text
    assert "LangGraph workflow" in text
    assert "Markdown or PDF" in text


def test_production_like_testing_runbook_is_wired():
    runbook = Path("docs/PRODUCTION_LIKE_TESTING.md").read_text(encoding="utf-8")
    makefile = Path("Makefile").read_text(encoding="utf-8")
    compose = Path("docker-compose.production.yml").read_text(encoding="utf-8")
    env_example = Path(".env.production.example").read_text(encoding="utf-8")
    gitignore = Path(".gitignore").read_text(encoding="utf-8")

    assert "make prod-up" in runbook
    assert "make prod-ingest-qdrant" in runbook
    assert "make prod-smoke" in runbook
    assert "OPENAI_API_KEY=replace-with-your-openai-api-key" in env_example
    assert "PLATFORM_API_KEY=change-me" in env_example
    assert ".env.production" in gitignore
    assert "docker compose --env-file .env.production -f docker-compose.production.yml up --build" in makefile
    assert "API_BASE_URL=http://127.0.0.1:8000 $(PYTHON) scripts/smoke_production_stack.py" in makefile

    for service in ["api:", "streamlit:", "react:", "mcp:", "postgres:", "qdrant:"]:
        assert service in compose
