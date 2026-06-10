from fastapi import APIRouter, Depends

from app.security import require_roles
from app.evaluation.run_eval import run_evaluation_suite

router = APIRouter(prefix="/evaluation", tags=["evaluation"], dependencies=[Depends(require_roles("auditor"))])


@router.get("/results")
def evaluation_results() -> list[dict]:
    return run_evaluation_suite()
