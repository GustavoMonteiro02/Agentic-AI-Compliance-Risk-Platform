from app.agents.graph import run_governance_assessment


def test_system_card_contains_required_sections():
    assessment = run_governance_assessment(
        "system-3",
        "AI assistant in HR analyzes CVs and ranks candidates for recruiters with human review.",
    )
    markdown = assessment.ai_system_card.content_markdown

    for section in ["Purpose", "Risk Classification", "Human Oversight", "Open Gaps", "Approval Status"]:
        assert section in markdown

