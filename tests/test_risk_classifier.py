from app.agents.graph import run_governance_assessment
from app.agents.nodes.risk_classifier import risk_classifier_node


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


def test_risk_classifier_preserves_deterministic_result_when_llm_fails(monkeypatch):
    class FailingProvider:
        provider_name = "openai_compatible"

        def advisory_completion(self, *_args, **_kwargs):
            raise RuntimeError("local model is not ready")

    monkeypatch.setattr("app.agents.nodes.risk_classifier.OptionalLLMProvider", FailingProvider)
    state = {
        "system_profile": {
            "business_domain": "employment",
            "personal_data": True,
            "sensitive_data": False,
            "decision_impact": "recommendation",
            "autonomy_level": "human-in-the-loop",
            "human_oversight": "human review",
            "missing_information": [],
        },
        "tool_calls": [],
    }

    updated = risk_classifier_node(state)

    assert updated["risk_classification"]["risk_level"] == "high"
    assert updated["tool_calls"][-1]["status"] == "failed"
    assert updated["tool_calls"][-1]["fallback"] == "deterministic_risk_preserved"
    assert updated["errors"][-1]["node"] == "risk_classifier"
