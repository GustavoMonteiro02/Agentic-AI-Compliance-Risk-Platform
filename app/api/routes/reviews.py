from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import DbSession
from app.api.pagination import PaginationParams, get_pagination, paginate
from app.schemas.notifications import NotificationEventRead
from app.schemas.review import ReviewDecision, ReviewQueueItem, ReviewRead
from app.security import AuthenticatedUser, require_roles
from app.services.notification_service import NotificationService
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"], dependencies=[Depends(require_roles("compliance_reviewer"))])


@router.get("/queue")
def review_queue(
    response: Response,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
    status: list[str] | None = Query(default=None),
    sla_hours: int | None = Query(default=None, ge=1, le=720),
    pagination: PaginationParams = Depends(get_pagination),
) -> list[ReviewQueueItem]:
    queue = ReviewService(db, user.tenant_id).queue(status, sla_hours=sla_hours)
    return paginate(queue, pagination, response)


@router.get("/escalations")
def review_escalations(
    response: Response,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
    sla_hours: int | None = Query(default=None, ge=1, le=720),
    pagination: PaginationParams = Depends(get_pagination),
) -> list[ReviewQueueItem]:
    escalations = ReviewService(db, user.tenant_id).escalations(sla_hours=sla_hours)
    return paginate(escalations, pagination, response)


@router.post("/escalations/notifications")
def queue_review_escalation_notifications(
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
    sla_hours: int | None = Query(default=None, ge=1, le=720),
    channel: str = Query(default="in_app"),
    recipient: str | None = Query(default=None),
) -> list[NotificationEventRead]:
    escalations = ReviewService(db, user.tenant_id).escalations(sla_hours=sla_hours)
    notifications = NotificationService(db, user.tenant_id).queue_review_escalations(
        escalations,
        recipient=recipient,
        channel=channel,
        user=user,
    )
    return [NotificationEventRead.model_validate(item) for item in notifications]


@router.get("/{assessment_id}/history")
def review_history(
    assessment_id: str,
    response: Response,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("compliance_reviewer"))],
    pagination: PaginationParams = Depends(get_pagination),
) -> list[ReviewRead]:
    history = ReviewService(db, user.tenant_id).history(assessment_id)
    return paginate(history, pagination, response)


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
