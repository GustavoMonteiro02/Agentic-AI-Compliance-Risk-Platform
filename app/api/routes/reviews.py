from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession
from app.schemas.review import ReviewDecision, ReviewQueueItem, ReviewRead
from app.security import require_roles
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"], dependencies=[Depends(require_roles("compliance_reviewer"))])


@router.get("/queue")
def review_queue(db: DbSession, status: list[str] | None = Query(default=None)) -> list[ReviewQueueItem]:
    return ReviewService(db).queue(status)


@router.get("/{assessment_id}/history")
def review_history(assessment_id: str, db: DbSession) -> list[ReviewRead]:
    return ReviewService(db).history(assessment_id)


@router.post("/{assessment_id}/approve")
def approve(assessment_id: str, payload: ReviewDecision, db: DbSession) -> dict:
    return ReviewService(db).decide(assessment_id, "approved", payload).model_dump()


@router.post("/{assessment_id}/reject")
def reject(assessment_id: str, payload: ReviewDecision, db: DbSession) -> dict:
    return ReviewService(db).decide(assessment_id, "rejected", payload).model_dump()


@router.post("/{assessment_id}/request-more-evidence")
def request_more_evidence(assessment_id: str, payload: ReviewDecision, db: DbSession) -> dict:
    return ReviewService(db).decide(assessment_id, "needs_more_evidence", payload).model_dump()
