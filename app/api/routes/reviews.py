from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession
from app.schemas.review import ReviewDecision, ReviewQueueItem, ReviewRead
from app.security import AuthenticatedUser, require_roles
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"], dependencies=[Depends(require_roles("compliance_reviewer"))])


@router.get("/queue")
def review_queue(
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
    status: list[str] | None = Query(default=None),
    sla_hours: int = Query(default=48, ge=1, le=720),
) -> list[ReviewQueueItem]:
    return ReviewService(db, user.tenant_id).queue(status, sla_hours=sla_hours)


@router.get("/escalations")
def review_escalations(
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
    sla_hours: int = Query(default=48, ge=1, le=720),
) -> list[ReviewQueueItem]:
    return ReviewService(db, user.tenant_id).escalations(sla_hours=sla_hours)


@router.get("/{assessment_id}/history")
def review_history(
    assessment_id: str,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
) -> list[ReviewRead]:
    return ReviewService(db, user.tenant_id).history(assessment_id)


@router.post("/{assessment_id}/approve")
def approve(
    assessment_id: str,
    payload: ReviewDecision,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
) -> dict:
    return ReviewService(db, user.tenant_id).decide(assessment_id, "approved", payload, user).model_dump()


@router.post("/{assessment_id}/reject")
def reject(
    assessment_id: str,
    payload: ReviewDecision,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
) -> dict:
    return ReviewService(db, user.tenant_id).decide(assessment_id, "rejected", payload, user).model_dump()


@router.post("/{assessment_id}/request-more-evidence")
def request_more_evidence(
    assessment_id: str,
    payload: ReviewDecision,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
) -> dict:
    return ReviewService(db, user.tenant_id).decide(assessment_id, "needs_more_evidence", payload, user).model_dump()
