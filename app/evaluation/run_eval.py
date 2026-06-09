from app.evaluation.evaluators import (
    evaluate_evidence_checklist_completeness,
    evaluate_human_approval_guardrail,
    evaluate_legal_advice_guardrail,
    evaluate_retrieval_grounding,
    evaluate_risk_classification,
    evaluate_system_card_section_coverage,
)


def run_evaluation_suite() -> list[dict]:
    return [
        evaluate_risk_classification(),
        evaluate_human_approval_guardrail(),
        evaluate_retrieval_grounding(),
        evaluate_system_card_section_coverage(),
        evaluate_evidence_checklist_completeness(),
        evaluate_legal_advice_guardrail(),
    ]
