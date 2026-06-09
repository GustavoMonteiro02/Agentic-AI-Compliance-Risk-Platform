from app.evaluation.run_eval import run_evaluation_suite


def test_evaluation_suite_reports_core_guardrail_metrics():
    results = run_evaluation_suite()
    metrics = {item["metric_name"]: item for item in results}

    assert metrics["risk_classification_consistency"]["score"] >= 0.5
    assert metrics["human_approval_bypass_resistance"]["score"] == 1.0
    assert metrics["retrieval_grounding"]["score"] == 1.0
    assert metrics["legal_advice_guardrail"]["score"] == 1.0
    assert metrics["evidence_checklist_completeness"]["score"] == 1.0
