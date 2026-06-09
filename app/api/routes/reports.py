from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.api.deps import DbSession
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{assessment_id}", response_class=PlainTextResponse)
def report_markdown(assessment_id: str, db: DbSession) -> str:
    return ReportService(db).audit_report_markdown(assessment_id)


@router.get("/{assessment_id}/system-card", response_class=PlainTextResponse)
def system_card_markdown(assessment_id: str, db: DbSession) -> str:
    return ReportService(db).system_card_markdown(assessment_id)
