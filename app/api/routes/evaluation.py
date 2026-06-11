from fastapi import APIRouter, Depends

from app.evaluation.run_eval import run_evaluation_suite
from app.observability.langsmith import build_langsmith_experiment_payload, upload_langsmith_experiment
from app.security import require_roles

router = APIRouter(prefix="/evaluation", tags=["evaluation"], dependencies=[Depends(require_roles("auditor"))])


@router.get("/results")
def evaluation_results() -> list[dict]:
    return run_evaluation_suite()


@router.get("/langsmith-experiment")
def langsmith_experiment_payload(experiment_name: str = "local-regression-suite") -> dict:
    return build_langsmith_experiment_payload(run_evaluation_suite(), experiment_name)


@router.post("/langsmith-experiment/upload")
def upload_langsmith_experiment_results(experiment_name: str = "local-regression-suite") -> dict:
    payload = build_langsmith_experiment_payload(run_evaluation_suite(), experiment_name)
    return upload_langsmith_experiment(payload)
