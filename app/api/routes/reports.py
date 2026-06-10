from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse, Response

from app.api.deps import DbSession
from app.security import require_roles
from app.services.pdf_service import markdown_to_simple_pdf
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(require_roles("viewer"))])


@router.get("/{assessment_id}.pdf")
def report_pdf(assessment_id: str, db: DbSession) -> Response:
    markdown = ReportService(db).audit_report_markdown(assessment_id)
    return Response(
        content=markdown_to_simple_pdf(markdown, "Audit Readiness Report"),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{assessment_id}_audit_report.pdf"'},
    )


@router.get("/{assessment_id}/system-card.pdf")
def system_card_pdf(assessment_id: str, db: DbSession) -> Response:
    markdown = ReportService(db).system_card_markdown(assessment_id)
    return Response(
        content=markdown_to_simple_pdf(markdown, "AI System Card"),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{assessment_id}_system_card.pdf"'},
    )


@router.get("/{assessment_id}", response_class=PlainTextResponse)
def report_markdown(assessment_id: str, db: DbSession) -> str:
    return ReportService(db).audit_report_markdown(assessment_id)


@router.get("/{assessment_id}/system-card", response_class=PlainTextResponse)
def system_card_markdown(assessment_id: str, db: DbSession) -> str:
    return ReportService(db).system_card_markdown(assessment_id)
