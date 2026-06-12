from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents.graph import run_governance_assessment
from app.config import get_settings
from app.database.repositories import AssessmentRepository, SystemRepository
from app.schemas.assessment import AssessmentRunRequest, GovernanceAssessment
from app.schemas.llm_usage import LLMUsageSummary
from app.schemas.remediation import RemediationAction, RemediationPlan
from app.services.llm_usage_service import summarize_llm_usage


def _due_date(priority: str) -> datetime:
    days = {"critical": 14, "high": 30, "medium": 60, "low": 90}.get(priority, 60)
    return datetime.utcnow() + timedelta(days=days)


class AssessmentService:
    def __init__(self, db: Session, tenant_id: str = "default") -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.systems = SystemRepository(db, tenant_id)
        self.assessments = AssessmentRepository(db, tenant_id)

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

    def llm_usage(self) -> LLMUsageSummary:
        settings = get_settings()
        return summarize_llm_usage(
            self.list(),
            prompt_cost_per_1k_tokens=settings.llm_prompt_cost_per_1k_tokens,
            completion_cost_per_1k_tokens=settings.llm_completion_cost_per_1k_tokens,
        )

    def assessment_llm_usage(self, assessment_id: str) -> LLMUsageSummary:
        settings = get_settings()
        assessment = self.get(assessment_id)
        return summarize_llm_usage(
            [assessment],
            prompt_cost_per_1k_tokens=settings.llm_prompt_cost_per_1k_tokens,
            completion_cost_per_1k_tokens=settings.llm_completion_cost_per_1k_tokens,
            assessment_id=assessment_id,
        )

    def remediation_plan(self, assessment_id: str) -> RemediationPlan:
        assessment = self.get(assessment_id)
        actions: list[RemediationAction] = []

        for gap in assessment.gap_analysis.critical_gaps:
            actions.append(
                RemediationAction(
                    title=gap.gap[:120],
                    description=gap.recommended_action,
                    priority="critical" if gap.risk.lower() == "high" else "high",
                    owner="Compliance",
                    due_date=_due_date("critical"),
                    source="critical_gap",
                )
            )
        for gap in assessment.gap_analysis.medium_gaps:
            actions.append(
                RemediationAction(
                    title=gap.gap[:120],
                    description=gap.recommended_action,
                    priority="medium",
                    owner="Compliance",
                    due_date=_due_date("medium"),
                    source="medium_gap",
                )
            )
        for item in assessment.evidence_checklist:
            if item.status != "missing":
                continue
            priority = "high" if item.priority == "high" else "medium"
            actions.append(
                RemediationAction(
                    title=f"Provide evidence: {item.evidence}"[:120],
                    description=f"Upload or approve evidence for {item.evidence}.",
                    priority=priority,
                    owner=item.owner,
                    due_date=_due_date(priority),
                    source="missing_evidence",
                )
            )

        priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        actions.sort(key=lambda action: (priority_order[action.priority], action.due_date), reverse=True)
        overall_priority = actions[0].priority if actions else "low"
        return RemediationPlan(
            assessment_id=assessment.id,
            system_id=assessment.system_id,
            overall_priority=overall_priority,
            actions=actions,
            evidence_gaps=sum(1 for item in assessment.evidence_checklist if item.status == "missing"),
            critical_gap_count=len(assessment.gap_analysis.critical_gaps),
            medium_gap_count=len(assessment.gap_analysis.medium_gaps),
        )
