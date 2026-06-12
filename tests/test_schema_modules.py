from app.schemas.controls import MappedControl
from app.schemas.audit import AuditEventRead
from app.schemas.report import GeneratedDocument
from app.schemas.llm_usage import LLMUsageSummary
from app.schemas.remediation import RemediationPlan
from app.schemas.risk_register import PolicyExceptionCreate, RiskRegisterItemUpdate
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
    assert LLMUsageSummary(total_tokens=10).total_tokens == 10
    assert RemediationPlan.model_fields["actions"]
    assert RiskRegisterItemUpdate(status="open").status == "open"
    exception = PolicyExceptionCreate(
        assessment_id="assessment-1",
        title="Exception",
        justification="Temporary business exception.",
        requested_by="Reviewer",
    )
    assert exception.compensating_controls == []
