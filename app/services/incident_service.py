from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import models
from app.database.repositories import AssessmentRepository
from app.schemas.incidents import IncidentCreate, IncidentUpdate
from app.security import AuthenticatedUser
from app.services.audit_service import AuditService


class IncidentService:
    def __init__(self, db: Session, tenant_id: str = "default") -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.assessments = AssessmentRepository(db, tenant_id)

    def _get_system(self, system_id: str) -> models.AISystem:
        system = self.db.scalar(
            select(models.AISystem)
            .where(models.AISystem.id == system_id, models.AISystem.tenant_id == self.tenant_id)
            .limit(1)
        )
        if not system:
            raise HTTPException(status_code=404, detail="AI system not found")
        return system

    def _get_incident(self, incident_id: str) -> models.AIIncident:
        incident = self.db.scalar(
            select(models.AIIncident)
            .where(models.AIIncident.id == incident_id, models.AIIncident.tenant_id == self.tenant_id)
            .limit(1)
        )
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        return incident

    def create(self, payload: IncidentCreate, user: AuthenticatedUser) -> models.AIIncident:
        self._get_system(payload.system_id)
        if payload.assessment_id and not self.assessments.get(payload.assessment_id):
            raise HTTPException(status_code=404, detail="Assessment not found")

        incident = models.AIIncident(
            tenant_id=self.tenant_id,
            system_id=payload.system_id,
            assessment_id=payload.assessment_id,
            title=payload.title,
            description=payload.description,
            severity=payload.severity,
            status="reported",
            owner=payload.owner,
            detected_at=payload.detected_at or datetime.utcnow(),
            impact_summary=payload.impact_summary,
            containment_actions_json=payload.containment_actions,
            regulatory_report_required=payload.regulatory_report_required,
        )
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        AuditService(self.db).record(
            user=user,
            action="incident.reported",
            resource_type="incident",
            resource_id=incident.id,
            assessment_id=incident.assessment_id,
            details={"severity": incident.severity, "system_id": incident.system_id},
        )
        return incident

    def list(self, status: str | None = None, severity: str | None = None) -> list[models.AIIncident]:
        statement = select(models.AIIncident).where(models.AIIncident.tenant_id == self.tenant_id)
        if status:
            statement = statement.where(models.AIIncident.status == status)
        if severity:
            statement = statement.where(models.AIIncident.severity == severity)
        return list(self.db.scalars(statement.order_by(models.AIIncident.detected_at.desc())))

    def update(self, incident_id: str, payload: IncidentUpdate, user: AuthenticatedUser) -> models.AIIncident:
        incident = self._get_incident(incident_id)
        changes = payload.model_dump(exclude_unset=True)
        if "containment_actions" in changes:
            incident.containment_actions_json = changes.pop("containment_actions")
        if "corrective_actions" in changes:
            incident.corrective_actions_json = changes.pop("corrective_actions")
        for key, value in changes.items():
            setattr(incident, key, value)
        if incident.status in {"resolved", "closed"} and incident.resolved_at is None:
            incident.resolved_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(incident)
        AuditService(self.db).record(
            user=user,
            action=f"incident.{incident.status}",
            resource_type="incident",
            resource_id=incident.id,
            assessment_id=incident.assessment_id,
            details={"severity": incident.severity, "owner": incident.owner},
        )
        return incident
