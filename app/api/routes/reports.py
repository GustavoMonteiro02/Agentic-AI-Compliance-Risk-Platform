from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.api.deps import DbSession
from app.services.assessment_service import AssessmentService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{assessment_id}", response_class=PlainTextResponse)
def report_markdown(assessment_id: str, db: DbSession) -> str:
    return AssessmentService(db).get(assessment_id).audit_report.content_markdown

