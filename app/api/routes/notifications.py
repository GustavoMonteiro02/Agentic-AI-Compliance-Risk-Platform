from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import DbSession
from app.api.pagination import PaginationParams, get_pagination, paginate
from app.schemas.notifications import NotificationDispatchResult, NotificationEventRead, NotificationEventUpdate
from app.security import AuthenticatedUser, require_roles
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"], dependencies=[Depends(require_roles("auditor"))])


@router.get("")
def list_notifications(
    response: Response,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("auditor"))],
    status: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    pagination: PaginationParams = Depends(get_pagination),
) -> list[NotificationEventRead]:
    notifications = [
        NotificationEventRead.model_validate(item)
        for item in NotificationService(db, user.tenant_id).list(status=status, event_type=event_type)
    ]
    return paginate(notifications, pagination, response)


@router.post("/dispatch")
def dispatch_notifications(
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("admin"))],
    event_type: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
) -> list[NotificationDispatchResult]:
    return NotificationService(db, user.tenant_id).dispatch_queued(
        event_type=event_type,
        limit=limit,
        user=user,
    )


@router.patch("/{notification_id}")
def update_notification(
    notification_id: str,
    payload: NotificationEventUpdate,
    db: DbSession,
    user: Annotated[AuthenticatedUser, Depends(require_roles("auditor"))],
) -> NotificationEventRead:
    return NotificationEventRead.model_validate(NotificationService(db, user.tenant_id).update(notification_id, payload, user))
