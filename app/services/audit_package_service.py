from __future__ import annotations

import json
from datetime import UTC, datetime
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session

from app.database import models


class AuditPackageService:
    def __init__(self, db: Session, tenant_id: str = "default") -> None:
        self.db = db
        self.tenant_id = tenant_id

    def build(self, assessment_id: str) -> dict:
        assessment = self._get_assessment(assessment_id)
        system = self._get_system(assessment.system_id)
        audit_report = self._first(
            models.AuditReport,
            models.AuditReport.assessment_id == assessment_id,
            order_by=models.AuditReport.created_at.desc(),
        )
        system_card = self._first(
            models.SystemCard,
            models.SystemCard.assessment_id == assessment_id,
            order_by=models.SystemCard.created_at.desc(),
        )

        package = {
            "manifest": {
                "package_type": "ai_governance_audit_package",
                "version": "2026-06-11.v1",
                "tenant_id": self.tenant_id,
                "assessment_id": assessment_id,
                "system_id": assessment.system_id,
                "generated_at": datetime.now(UTC).isoformat(),
                "contents": [
                    "system",
                    "assessment",
                    "mapped_controls",
                    "compliance_gaps",
                    "evidence_items",
                    "risk_register_items",
                    "policy_exceptions",
                    "incidents",
                    "human_reviews",
                    "tool_calls",
                    "audit_events",
                    "notification_events",
                    "system_card",
                    "audit_report",
                ],
            },
            "system": self._to_dict(system),
            "assessment": self._to_dict(assessment),
            "mapped_controls": self._list(
                models.MappedControlRecord,
                models.MappedControlRecord.assessment_id == assessment_id,
            ),
            "compliance_gaps": self._list(models.ComplianceGap, models.ComplianceGap.assessment_id == assessment_id),
            "evidence_items": self._list(
                models.EvidenceItemRecord,
                models.EvidenceItemRecord.assessment_id == assessment_id,
            ),
            "risk_register_items": self._list(
                models.RiskRegisterItem,
                models.RiskRegisterItem.assessment_id == assessment_id,
                models.RiskRegisterItem.tenant_id == self.tenant_id,
            ),
            "policy_exceptions": self._list(
                models.PolicyException,
                models.PolicyException.assessment_id == assessment_id,
                models.PolicyException.tenant_id == self.tenant_id,
            ),
            "incidents": self._list(
                models.AIIncident,
                models.AIIncident.assessment_id == assessment_id,
                models.AIIncident.tenant_id == self.tenant_id,
            ),
            "human_reviews": self._list(models.HumanReview, models.HumanReview.assessment_id == assessment_id),
            "tool_calls": self._list(models.ToolCall, models.ToolCall.assessment_id == assessment_id),
            "audit_events": self._list(
                models.AuditEvent,
                models.AuditEvent.assessment_id == assessment_id,
                models.AuditEvent.tenant_id == self.tenant_id,
            ),
            "notification_events": self._list(
                models.NotificationEvent,
                models.NotificationEvent.assessment_id == assessment_id,
                models.NotificationEvent.tenant_id == self.tenant_id,
            ),
            "system_card": self._to_dict(system_card) if system_card else None,
            "audit_report": self._to_dict(audit_report) if audit_report else None,
        }
        package["summary"] = self._summary(package)
        return package

    def build_tenant_export(self) -> dict:
        assessments = self._list(models.RiskAssessment, models.RiskAssessment.tenant_id == self.tenant_id)
        assessment_packages = [self.build(assessment["id"]) for assessment in assessments]
        systems = self._list(models.AISystem, models.AISystem.tenant_id == self.tenant_id)
        export = {
            "manifest": {
                "package_type": "ai_governance_tenant_export",
                "version": "2026-06-12.v1",
                "tenant_id": self.tenant_id,
                "generated_at": datetime.now(UTC).isoformat(),
                "assessment_count": len(assessment_packages),
                "system_count": len(systems),
                "contents": [
                    "systems",
                    "assessments",
                    "assessment_packages",
                    "risk_register_items",
                    "policy_exceptions",
                    "incidents",
                    "audit_events",
                    "notification_events",
                ],
            },
            "systems": systems,
            "assessments": assessments,
            "assessment_packages": assessment_packages,
            "risk_register_items": self._list(models.RiskRegisterItem, models.RiskRegisterItem.tenant_id == self.tenant_id),
            "policy_exceptions": self._list(models.PolicyException, models.PolicyException.tenant_id == self.tenant_id),
            "incidents": self._list(models.AIIncident, models.AIIncident.tenant_id == self.tenant_id),
            "audit_events": self._list(models.AuditEvent, models.AuditEvent.tenant_id == self.tenant_id),
            "notification_events": self._list(
                models.NotificationEvent,
                models.NotificationEvent.tenant_id == self.tenant_id,
            ),
        }
        export["summary"] = {
            "system_count": len(export["systems"]),
            "assessment_count": len(export["assessments"]),
            "risk_count": len(export["risk_register_items"]),
            "incident_count": len(export["incidents"]),
            "audit_event_count": len(export["audit_events"]),
            "notification_event_count": len(export["notification_events"]),
        }
        return export

    def build_zip(self, assessment_id: str) -> bytes:
        package = self.build(assessment_id)
        payload = json.dumps(package, indent=2, sort_keys=True)
        buffer = BytesIO()
        with ZipFile(buffer, mode="w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(package["manifest"], indent=2, sort_keys=True))
            archive.writestr("audit_package.json", payload)
            if package["audit_report"]:
                archive.writestr("reports/audit_report.md", package["audit_report"]["content_markdown"])
            if package["system_card"]:
                archive.writestr("reports/system_card.md", package["system_card"]["content_markdown"])
        return buffer.getvalue()

    def build_tenant_export_zip(self) -> bytes:
        export = self.build_tenant_export()
        buffer = BytesIO()
        with ZipFile(buffer, mode="w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(export["manifest"], indent=2, sort_keys=True))
            archive.writestr("tenant_export.json", json.dumps(export, indent=2, sort_keys=True))
            for package in export["assessment_packages"]:
                assessment_id = package["manifest"]["assessment_id"]
                archive.writestr(
                    f"assessments/{assessment_id}/audit_package.json",
                    json.dumps(package, indent=2, sort_keys=True),
                )
                if package["audit_report"]:
                    archive.writestr(
                        f"assessments/{assessment_id}/audit_report.md",
                        package["audit_report"]["content_markdown"],
                    )
                if package["system_card"]:
                    archive.writestr(
                        f"assessments/{assessment_id}/system_card.md",
                        package["system_card"]["content_markdown"],
                    )
        return buffer.getvalue()

    def _get_assessment(self, assessment_id: str) -> models.RiskAssessment:
        assessment = self.db.scalar(
            select(models.RiskAssessment)
            .where(models.RiskAssessment.id == assessment_id, models.RiskAssessment.tenant_id == self.tenant_id)
            .limit(1)
        )
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        return assessment

    def _get_system(self, system_id: str) -> models.AISystem:
        system = self.db.scalar(
            select(models.AISystem)
            .where(models.AISystem.id == system_id, models.AISystem.tenant_id == self.tenant_id)
            .limit(1)
        )
        if not system:
            raise HTTPException(status_code=404, detail="System not found")
        return system

    def _first(self, model, *conditions, order_by=None):
        statement = select(model).where(*conditions)
        if order_by is not None:
            statement = statement.order_by(order_by)
        return self.db.scalar(statement.limit(1))

    def _list(self, model, *conditions) -> list[dict]:
        statement = select(model).where(*conditions)
        if hasattr(model, "created_at"):
            statement = statement.order_by(model.created_at.asc())
        return [self._to_dict(record) for record in self.db.scalars(statement)]

    def _to_dict(self, record) -> dict:
        values = {}
        for column in inspect(record).mapper.column_attrs:
            value = getattr(record, column.key)
            if isinstance(value, datetime):
                value = value.isoformat()
            values[column.key] = value
        return values

    def _summary(self, package: dict) -> dict:
        evidence = package["evidence_items"]
        gaps = package["compliance_gaps"]
        risks = package["risk_register_items"]
        incidents = package["incidents"]
        return {
            "risk_level": package["assessment"]["risk_level"],
            "assessment_status": package["assessment"]["status"],
            "control_count": len(package["mapped_controls"]),
            "open_gap_count": len([gap for gap in gaps if gap["status"] == "open"]),
            "missing_evidence_count": len([item for item in evidence if item["status"] != "approved"]),
            "open_risk_count": len([risk for risk in risks if risk["status"] not in {"closed", "accepted"}]),
            "open_incident_count": len(
                [incident for incident in incidents if incident["status"] not in {"resolved", "closed"}]
            ),
            "audit_event_count": len(package["audit_events"]),
            "notification_event_count": len(package["notification_events"]),
        }
