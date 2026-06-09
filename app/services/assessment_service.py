from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents.graph import run_governance_assessment
from app.database.repositories import AssessmentRepository, SystemRepository
from app.schemas.assessment import AssessmentRunRequest, GovernanceAssessment


class AssessmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.systems = SystemRepository(db)
        self.assessments = AssessmentRepository(db)

    def assess_system(self, system_id: str, payload: AssessmentRunRequest | None = None) -> GovernanceAssessment:
        system = self.systems.get(system_id)
        if not system:
            raise HTTPException(status_code=404, detail="AI system not found")
        request = payload or AssessmentRunRequest()
        context = {
            "name": system.name,
            "business_unit": system.business_unit,
            "owner": system.owner,
            "technical_owner": system.technical_owner,
            "deployment_status": system.deployment_status,
            "users_affected": system.users_affected,
            "data_types": system.data_types,
            "model_provider": system.model_provider,
            "model_type": system.model_type,
            "decision_impact": system.decision_impact,
            "autonomy_level": system.autonomy_level,
            "human_oversight_process": system.human_oversight_process,
            "external_users_affected": (system.system_metadata or {}).get("external_users_affected", False),
            "integrations_tools_used": (system.system_metadata or {}).get("integrations_tools_used", []),
            "monitoring_status": (system.system_metadata or {}).get("monitoring_status"),
            "evaluation_status": (system.system_metadata or {}).get("evaluation_status"),
            "security_testing_status": (system.system_metadata or {}).get("security_testing_status"),
            **request.additional_context,
        }
        assessment = run_governance_assessment(
            system.id,
            system.description,
            system_context=context,
            user_answers=[item.model_dump() for item in request.user_answers],
        )
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
