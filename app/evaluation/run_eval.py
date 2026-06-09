from app.evaluation.evaluators import evaluate_human_approval_guardrail, evaluate_risk_classification


def run_evaluation_suite() -> list[dict]:
    return [evaluate_risk_classification(), evaluate_human_approval_guardrail()]

