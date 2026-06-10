from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import models
from app.schemas.assessment import GovernanceAssessment
from app.schemas.system import AISystemCreate, AISystemUpdate


def _evidence_due_date(priority: str) -> datetime:
    days_by_priority = {"high": 14, "medium": 30, "low": 60}
    return datetime.utcnow() + timedelta(days=days_by_priority.get(priority, 30))


class SystemRepository:
    def __init__(self, db: Session, tenant_id: str = "default") -> None:
        self.db = db
        self.tenant_id = tenant_id

    def create(self, payload: AISystemCreate) -> models.AISystem:
        system_metadata = {
            **payload.metadata,
            "external_users_affected": payload.external_users_affected,
            "integrations_tools_used": payload.integrations_tools_used,
            "monitoring_status": payload.monitoring_status,
            "evaluation_status": payload.evaluation_status,
            "security_testing_status": payload.security_testing_status,
        }
        system = models.AISystem(
            tenant_id=self.tenant_id,
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
            system_metadata=system_metadata,
        )
        self.db.add(system)
        self.db.commit()
        self.db.refresh(system)
        return system

    def list(self) -> list[models.AISystem]:
        return list(
            self.db.scalars(
                select(models.AISystem)
                .where(models.AISystem.tenant_id == self.tenant_id)
                .order_by(models.AISystem.created_at.desc())
            )
        )

    def get(self, system_id: str) -> models.AISystem | None:
        return self.db.scalar(
            select(models.AISystem)
            .where(models.AISystem.id == system_id, models.AISystem.tenant_id == self.tenant_id)
            .limit(1)
        )

    def update(self, system: models.AISystem, payload: AISystemUpdate) -> models.AISystem:
        values = payload.model_dump(exclude_unset=True)
        metadata_value = values.pop("metadata", None)
        metadata_fields = {
            key: values.pop(key)
            for key in [
                "external_users_affected",
                "integrations_tools_used",
                "monitoring_status",
                "evaluation_status",
                "security_testing_status",
            ]
            if key in values
        }
        for key, value in values.items():
            setattr(system, key, value)
        if metadata_value is not None or metadata_fields:
            system.system_metadata = {**(system.system_metadata or {}), **(metadata_value or {}), **metadata_fields}
        self.db.commit()
        self.db.refresh(system)
        return system


class AssessmentRepository:
    def __init__(self, db: Session, tenant_id: str = "default") -> None:
        self.db = db
        self.tenant_id = tenant_id

    def save(self, assessment: GovernanceAssessment) -> models.RiskAssessment:
        record = models.RiskAssessment(
            id=assessment.id,
            tenant_id=self.tenant_id,
            system_id=assessment.system_id,
            risk_level=assessment.risk_classification.risk_level,
            confidence=assessment.risk_classification.confidence,
            risk_factors_json=assessment.risk_classification.risk_factors,
            reasoning_summary=assessment.risk_classification.reasoning_summary,
            assessment_json=assessment.model_dump(mode="json"),
            status=assessment.status,
        )
        self.db.add(record)
        self.db.add(
            models.AISystemProfile(
                tenant_id=self.tenant_id,
                system_id=assessment.system_id,
                profile_json=assessment.profile.model_dump(),
            )
        )
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
                    due_date=_evidence_due_date(item.priority),
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
        return self.db.scalar(
            select(models.RiskAssessment)
            .where(models.RiskAssessment.id == assessment_id, models.RiskAssessment.tenant_id == self.tenant_id)
            .limit(1)
        )

    def latest_for_system(self, system_id: str) -> models.RiskAssessment | None:
        return self.db.scalar(
            select(models.RiskAssessment)
            .where(
                models.RiskAssessment.system_id == system_id,
                models.RiskAssessment.tenant_id == self.tenant_id,
            )
            .order_by(models.RiskAssessment.created_at.desc())
            .limit(1)
        )

    def list(self) -> list[models.RiskAssessment]:
        return list(
            self.db.scalars(
                select(models.RiskAssessment)
                .where(models.RiskAssessment.tenant_id == self.tenant_id)
                .order_by(models.RiskAssessment.created_at.desc())
            )
        )

    def list_by_status(self, statuses: list[str]) -> list[models.RiskAssessment]:
        return list(
            self.db.scalars(
                select(models.RiskAssessment)
                .where(
                    models.RiskAssessment.status.in_(statuses),
                    models.RiskAssessment.tenant_id == self.tenant_id,
                )
                .order_by(models.RiskAssessment.created_at.desc())
            )
        )

    def update_status(self, assessment: models.RiskAssessment, status: str, notes: str | None = None) -> None:
        data = dict(assessment.assessment_json)
        data["status"] = status
        data["human_review_status"] = status
        data["human_review_notes"] = notes
        assessment.status = status
        assessment.assessment_json = data
        self.db.commit()
