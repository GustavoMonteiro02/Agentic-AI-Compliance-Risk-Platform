from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import models
from app.database.repositories import AssessmentRepository
from app.schemas.risk_register import PolicyExceptionCreate, PolicyExceptionUpdate, RiskRegisterItemUpdate
from app.security import AuthenticatedUser
from app.services.audit_service import AuditService


def _risk_due_date(severity: str) -> datetime:
    return datetime.utcnow() + timedelta(days=30 if severity.lower() == "high" else 60)


class RiskRegisterService:
    def __init__(self, db: Session, tenant_id: str = "default") -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.assessments = AssessmentRepository(db, tenant_id)

    def sync_from_assessment(self, assessment_id: str, user: AuthenticatedUser) -> list[models.RiskRegisterItem]:
        assessment = self.assessments.get(assessment_id)
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        data = assessment.assessment_json
        gaps = data["gap_analysis"]["critical_gaps"] + data["gap_analysis"]["medium_gaps"]
        created: list[models.RiskRegisterItem] = []
        for gap in gaps:
            existing = self.db.scalar(
                select(models.RiskRegisterItem)
                .where(
                    models.RiskRegisterItem.tenant_id == self.tenant_id,
                    models.RiskRegisterItem.assessment_id == assessment_id,
                    models.RiskRegisterItem.source_gap == gap["gap"],
                )
                .limit(1)
            )
            if existing:
                created.append(existing)
                continue
            severity = "high" if gap["risk"].lower() == "high" else "medium"
            item = models.RiskRegisterItem(
                tenant_id=self.tenant_id,
                assessment_id=assessment_id,
                system_id=assessment.system_id,
                title=gap["gap"][:255],
                description=gap["recommended_action"],
                severity=severity,
                likelihood="medium",
                impact="high" if severity == "high" else "medium",
                owner="Compliance",
                status="open",
                mitigation_plan=gap["recommended_action"],
                source_gap=gap["gap"],
                due_date=_risk_due_date(severity),
            )
            self.db.add(item)
            created.append(item)
        self.db.commit()
        for item in created:
            self.db.refresh(item)
        AuditService(self.db).record(
            user=user,
            action="risk_register.synced",
            resource_type="assessment",
            resource_id=assessment_id,
            assessment_id=assessment_id,
            details={"risk_count": len(created)},
        )
        return created

    def list(self) -> list[models.RiskRegisterItem]:
        return list(
            self.db.scalars(
                select(models.RiskRegisterItem)
                .where(models.RiskRegisterItem.tenant_id == self.tenant_id)
                .order_by(models.RiskRegisterItem.created_at.desc())
            )
        )

    def update(self, item_id: str, payload: RiskRegisterItemUpdate, user: AuthenticatedUser) -> models.RiskRegisterItem:
        item = self.db.scalar(
            select(models.RiskRegisterItem)
            .where(models.RiskRegisterItem.id == item_id, models.RiskRegisterItem.tenant_id == self.tenant_id)
            .limit(1)
        )
        if not item:
            raise HTTPException(status_code=404, detail="Risk register item not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, key, value)
        self.db.commit()
        self.db.refresh(item)
        AuditService(self.db).record(
            user=user,
            action="risk_register.updated",
            resource_type="risk_register_item",
            resource_id=item.id,
            assessment_id=item.assessment_id,
            details={"status": item.status, "owner": item.owner},
        )
        return item


class PolicyExceptionService:
    def __init__(self, db: Session, tenant_id: str = "default") -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.assessments = AssessmentRepository(db, tenant_id)

    def create(self, payload: PolicyExceptionCreate, user: AuthenticatedUser) -> models.PolicyException:
        assessment = self.assessments.get(payload.assessment_id)
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        exception = models.PolicyException(
            tenant_id=self.tenant_id,
            assessment_id=payload.assessment_id,
            system_id=assessment.system_id,
            requirement_id=payload.requirement_id,
            title=payload.title,
            justification=payload.justification,
            compensating_controls_json=payload.compensating_controls,
            requested_by=payload.requested_by,
            status="requested",
            expires_at=payload.expires_at,
        )
        self.db.add(exception)
        self.db.commit()
        self.db.refresh(exception)
        AuditService(self.db).record(
            user=user,
            action="policy_exception.requested",
            resource_type="policy_exception",
            resource_id=exception.id,
            assessment_id=exception.assessment_id,
            details={"title": exception.title, "requirement_id": exception.requirement_id},
        )
        return exception

    def list(self) -> list[models.PolicyException]:
        return list(
            self.db.scalars(
                select(models.PolicyException)
                .where(models.PolicyException.tenant_id == self.tenant_id)
                .order_by(models.PolicyException.created_at.desc())
            )
        )

    def update(self, exception_id: str, payload: PolicyExceptionUpdate, user: AuthenticatedUser) -> models.PolicyException:
        exception = self.db.scalar(
            select(models.PolicyException)
            .where(models.PolicyException.id == exception_id, models.PolicyException.tenant_id == self.tenant_id)
            .limit(1)
        )
        if not exception:
            raise HTTPException(status_code=404, detail="Policy exception not found")
        exception.status = payload.status
        if payload.approved_by is not None:
            exception.approved_by = payload.approved_by
        if payload.compensating_controls is not None:
            exception.compensating_controls_json = payload.compensating_controls
        if payload.expires_at is not None:
            exception.expires_at = payload.expires_at
        self.db.commit()
        self.db.refresh(exception)
        AuditService(self.db).record(
            user=user,
            action=f"policy_exception.{exception.status}",
            resource_type="policy_exception",
            resource_id=exception.id,
            assessment_id=exception.assessment_id,
            details={"approved_by": exception.approved_by, "status": exception.status},
        )
        return exception
