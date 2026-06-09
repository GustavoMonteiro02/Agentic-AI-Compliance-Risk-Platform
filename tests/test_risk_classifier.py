from app.agents.graph import run_governance_assessment


def test_hr_cv_screening_classified_as_high_risk_candidate():
    assessment = run_governance_assessment(
        "system-1",
        "AI assistant in HR analyzes CVs, ranks candidates, processes personal data, "
        "and recommends candidates to recruiters. Humans review final hiring decisions.",
    )

    assert assessment.risk_classification.risk_level == "high"
    assert assessment.risk_classification.requires_human_review is True
    assert "personal data processing" in assessment.risk_classification.risk_factors


def test_customer_support_copilot_requires_human_approval_for_refund_decisions():
    assessment = run_governance_assessment(
        "system-2",
        "Customer support AI copilot summarizes tickets and suggests refunds for agents. "
        "A supervisor reviews refund decisions.",
    )

    assert assessment.status == "needs_review"
    assert assessment.human_review_status == "needs_review"
    assert assessment.requires_human_review is True

