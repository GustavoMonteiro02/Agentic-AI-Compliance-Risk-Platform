from app.agents.graph import run_governance_assessment


def test_gap_analysis_detects_missing_evaluation_dataset():
    assessment = run_governance_assessment(
        "system-4",
        "AI assistant in HR analyzes CVs and recommends candidates to recruiters.",
    )
    gaps = assessment.gap_analysis.critical_gaps + assessment.gap_analysis.medium_gaps

    assert any("Evaluation" in gap.gap or "evaluation" in gap.recommended_action.lower() for gap in gaps)

