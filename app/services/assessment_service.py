from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents.graph import run_governance_assessment
from app.database.repositories import AssessmentRepository, SystemRepository
from app.schemas.assessment import GovernanceAssessment


class AssessmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.systems = SystemRepository(db)
        self.assessments = AssessmentRepository(db)

    def assess_system(self, system_id: str) -> GovernanceAssessment:
        system = self.systems.get(system_id)
        if not system:
            raise HTTPException(status_code=404, detail="AI system not found")
        assessment = run_governance_assessment(system.id, system.description)
        self.assessments.save(assessment)
        return assessment

    def get(self, assessment_id: str) -> GovernanceAssessment:
        record = self.assessments.get(assessment_id)
        if not record:
            raise HTTPException(status_code=404, detail="Assessment not found")
        return GovernanceAssessment.model_validate(record.assessment_json)

    def latest_for_system(self, system_id: str) -> GovernanceAssessment:
        record = self.assessments.latest_for_system(system_id)
        if not record:
            raise HTTPException(status_code=404, detail="Assessment not found")
        return GovernanceAssessment.model_validate(record.assessment_json)

    def list(self) -> list[GovernanceAssessment]:
        return [GovernanceAssessment.model_validate(item.assessment_json) for item in self.assessments.list()]

