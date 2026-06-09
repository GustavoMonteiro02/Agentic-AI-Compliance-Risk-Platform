from fastapi import APIRouter

from app.evaluation.run_eval import run_evaluation_suite

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.get("/results")
def evaluation_results() -> list[dict]:
    return run_evaluation_suite()

