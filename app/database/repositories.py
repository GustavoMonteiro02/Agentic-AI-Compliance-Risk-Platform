from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import models
from app.schemas.assessment import GovernanceAssessment
from app.schemas.system import AISystemCreate, AISystemUpdate


class SystemRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: AISystemCreate) -> models.AISystem:
        system = models.AISystem(
            name=payload.name,
            description=payload.description,
            business_unit=payload.business_unit,
            owner=payload.owner,
            technical_owner=payload.technical_owner,
            deployment_status=payload.deployment_status,
            users_affected=payload.users_affected,
            data_types=payload.data_types,
            model_provider=payload.model_provider,
            model_type=payload.model_type,
            decision_impact=payload.decision_impact,
            autonomy_level=payload.autonomy_level,
            human_oversight_process=payload.human_oversight_process,
            system_metadata=payload.metadata,
        )
        self.db.add(system)
        self.db.commit()
        self.db.refresh(system)
        return system

    def list(self) -> list[models.AISystem]:
        return list(self.db.scalars(select(models.AISystem).order_by(models.AISystem.created_at.desc())))

    def get(self, system_id: str) -> models.AISystem | None:
        return self.db.get(models.AISystem, system_id)

    def update(self, system: models.AISystem, payload: AISystemUpdate) -> models.AISystem:
        values = payload.model_dump(exclude_unset=True)
        metadata_value = values.pop("metadata", None)
        for key, value in values.items():
            setattr(system, key, value)
        if metadata_value is not None:
            system.system_metadata = metadata_value
        self.db.commit()
        self.db.refresh(system)
        return system


class AssessmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def save(self, assessment: GovernanceAssessment) -> models.RiskAssessment:
        record = models.RiskAssessment(
            id=assessment.id,
            system_id=assessment.system_id,
            risk_level=assessment.risk_classification.risk_level,
            confidence=assessment.risk_classification.confidence,
            risk_factors_json=assessment.risk_classification.risk_factors,
            reasoning_summary=assessment.risk_classification.reasoning_summary,
            assessment_json=assessment.model_dump(mode="json"),
            status=assessment.status,
        )
        self.db.add(record)
        self.db.add(models.AISystemProfile(system_id=assessment.system_id, profile_json=assessment.profile.model_dump()))
        for control in assessment.mapped_controls:
            self.db.add(
                models.MappedControlRecord(
                    assessment_id=assessment.id,
                    requirement_id=control.requirement_id,
                    control_name=control.requirement,
                    control_description=control.mapped_control,
                    control_status=control.control_status,
                    evidence_needed_json=control.evidence_needed,
                )
            )
        for gap in assessment.gap_analysis.critical_gaps + assessment.gap_analysis.medium_gaps:
            self.db.add(
                models.ComplianceGap(
                    assessment_id=assessment.id,
                    gap_title=gap.gap[:255],
                    gap_description=gap.gap,
                    severity=gap.risk,
                    recommended_action=gap.recommended_action,
                )
            )
        for item in assessment.evidence_checklist:
            self.db.add(
                models.EvidenceItemRecord(
                    assessment_id=assessment.id,
                    name=item.evidence,
                    priority=item.priority,
                    owner=item.owner,
                    status=item.status,
                    description="",
                )
            )
        self.db.add(
            models.SystemCard(
                system_id=assessment.system_id,
                assessment_id=assessment.id,
                content_markdown=assessment.ai_system_card.content_markdown,
                content_json=assessment.ai_system_card.content_json,
                status=assessment.ai_system_card.status,
            )
        )
        self.db.add(
            models.AuditReport(
                assessment_id=assessment.id,
                content_markdown=assessment.audit_report.content_markdown,
                content_json=assessment.audit_report.content_json,
                status=assessment.audit_report.status,
            )
        )
        for call in assessment.tool_calls:
            self.db.add(
                models.ToolCall(
                    assessment_id=assessment.id,
                    tool_name=call.get("tool_name", "unknown"),
                    tool_result_json=call,
                    status=call.get("status", "success"),
                )
            )
        self.db.commit()
        self.db.refresh(record)
        return record

    def get(self, assessment_id: str) -> models.RiskAssessment | None:
        return self.db.get(models.RiskAssessment, assessment_id)

    def latest_for_system(self, system_id: str) -> models.RiskAssessment | None:
        return self.db.scalar(
            select(models.RiskAssessment)
            .where(models.RiskAssessment.system_id == system_id)
            .order_by(models.RiskAssessment.created_at.desc())
            .limit(1)
        )

    def list(self) -> list[models.RiskAssessment]:
        return list(self.db.scalars(select(models.RiskAssessment).order_by(models.RiskAssessment.created_at.desc())))

    def update_status(self, assessment: models.RiskAssessment, status: str, notes: str | None = None) -> None:
        data = dict(assessment.assessment_json)
        data["status"] = status
        data["human_review_status"] = status
        data["human_review_notes"] = notes
        assessment.status = status
        assessment.assessment_json = data
        self.db.commit()

