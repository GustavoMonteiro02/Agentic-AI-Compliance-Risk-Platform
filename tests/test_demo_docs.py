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
