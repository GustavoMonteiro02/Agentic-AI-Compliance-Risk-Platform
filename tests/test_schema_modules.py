from app.schemas.controls import MappedControl
from app.schemas.audit import AuditEventRead
from app.schemas.report import GeneratedDocument
from app.schemas.risk import RiskClassification


def test_schema_layout_exports_expected_models():
    risk = RiskClassification(
        risk_level="high",
        confidence=0.9,
        risk_factors=["employment context"],
        reasoning_summary="Human review required.",
    )
    control = MappedControl(
        requirement_id="REQ_1",
        requirement="Human oversight",
        mapped_control="Reviewer approval is required.",
    )
    document = GeneratedDocument(title="Report", content_markdown="# Report")

    assert risk.requires_human_review is True
    assert control.control_status == "unknown"
    assert document.status == "draft"
    assert AuditEventRead.model_fields["action"]
