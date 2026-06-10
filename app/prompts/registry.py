from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    version: str
    system: str
    user_template: str


LLM_REFINER_PROMPT = PromptTemplate(
    name="llm_refiner",
    version="2026-06-10.v1",
    system="""You are an AI governance and compliance engineering assistant.
You help prepare audit-readiness drafts, not legal advice.
Never claim final compliance. Always require qualified human review.
Return only valid JSON matching the requested keys.""",
    user_template="""
Refine this governance assessment as production-quality structured output.

Return JSON with exactly these keys:
- risk_classification: object with risk_level, confidence, risk_factors, reasoning_summary, requires_human_review, requires_additional_information
- mapped_controls: array of objects with requirement_id, requirement, mapped_control, evidence_needed, control_status
- gap_analysis: object with overall_status, critical_gaps, medium_gaps, low_gaps, priority_actions
- evidence_checklist: array of objects with evidence, status, priority, owner
- ai_system_card_markdown: markdown string
- audit_report_markdown: markdown string

Keep all analysis preliminary. Do not provide legal advice. Require human review.
Ground recommendations in the retrieved requirements and preserve citation/source details when they are present.

Assessment:
{assessment_json}
""",
)


PROMPT_REGISTRY = {
    LLM_REFINER_PROMPT.name: LLM_REFINER_PROMPT,
}


def get_prompt(name: str) -> PromptTemplate:
    return PROMPT_REGISTRY[name]
