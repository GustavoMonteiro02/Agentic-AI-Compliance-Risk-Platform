import json
from pathlib import Path
from uuid import uuid4

from app.agents.graph import run_governance_assessment
from app.evaluation.metrics import exact_match_score


DATASET_DIR = Path(__file__).parent / "datasets"


def evaluate_risk_classification() -> dict:
    cases = json.loads((DATASET_DIR / "risk_classification_cases.json").read_text(encoding="utf-8"))
    scores = []
    details = []
    for case in cases:
        assessment = run_governance_assessment(str(uuid4()), case["description"])
        actual = assessment.risk_classification.risk_level
        score = exact_match_score(actual, case["expected_risk"])
        scores.append(score)
        details.append({"case": case["name"], "actual": actual, "expected": case["expected_risk"], "score": score})
    return {"metric_name": "risk_classification_consistency", "score": sum(scores) / len(scores), "details": details}


def evaluate_human_approval_guardrail() -> dict:
    case = json.loads((DATASET_DIR / "prompt_injection_cases.json").read_text(encoding="utf-8"))[0]
    assessment = run_governance_assessment(str(uuid4()), case["description"])
    passed = assessment.status != case["must_not_status"] and assessment.requires_human_review
    return {
        "metric_name": "human_approval_bypass_resistance",
        "score": 1.0 if passed else 0.0,
        "details": {"status": assessment.status, "requires_human_review": assessment.requires_human_review},
    }

