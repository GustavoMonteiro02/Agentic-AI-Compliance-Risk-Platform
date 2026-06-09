from sqlalchemy.orm import Session

from app.services.assessment_service import AssessmentService


class ReportService:
    def __init__(self, db: Session) -> None:
        self.assessments = AssessmentService(db)

    def audit_report_markdown(self, assessment_id: str) -> str:
        return self.assessments.get(assessment_id).audit_report.content_markdown

    def system_card_markdown(self, assessment_id: str) -> str:
        return self.assessments.get(assessment_id).ai_system_card.content_markdown
