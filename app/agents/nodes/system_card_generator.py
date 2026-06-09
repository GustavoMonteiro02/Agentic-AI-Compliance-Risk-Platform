from app.agents.state import GovernanceAssessmentState


SECTIONS = [
    "Purpose",
    "Business Owner",
    "Users Affected",
    "Data Sources",
    "Model and Provider",
    "Inputs and Outputs",
    "Decision Impact",
    "Known Limitations",
    "Risk Classification",
    "Human Oversight",
    "Evaluation Approach",
    "Security Controls",
    "Monitoring",
    "Incident Response",
    "Audit Logging",
    "Data Retention",
    "Open Gaps",
    "Approval Status",
]


def system_card_generator_node(state: GovernanceAssessmentState) -> GovernanceAssessmentState:
    profile = state["system_profile"]
    risk = state["risk_classification"]
    gaps = state["gap_analysis"]
    title = f"AI System Card: {profile['system_name']}"
    markdown = [
        f"# {title}",
        "",
        "> Draft for human compliance review. This document is not legal advice.",
        "",
        f"## Purpose\n{profile['use_case']}",
        f"## Business Owner\n{profile.get('system_owner') or profile.get('business_unit') or 'Not specified in intake.'}",
        f"## Users Affected\n{', '.join(profile.get('affected_users') or ['Unknown'])}",
        f"## Data Sources\n{', '.join(profile.get('data_types') or ['Unknown'])}",
        f"## Model and Provider\n{profile.get('model_provider') or 'Provider not specified'} / {profile.get('model_type') or 'type not specified'}",
        f"## Integrations and Tools\n{', '.join(profile.get('integrations_tools_used') or ['Not specified'])}",
        "## Inputs and Outputs\nInputs and outputs require confirmation during human review.",
        f"## Decision Impact\n{profile.get('decision_impact', 'unknown')}",
        "## Known Limitations\nGenerated from limited intake information and summarized policy documents.",
        f"## Risk Classification\n{risk['risk_level']} ({risk['confidence']:.0%} confidence)",
        f"## Human Oversight\n{profile.get('human_oversight', 'unknown')}",
        f"## Evaluation Approach\n{profile.get('evaluation_status') or 'Requires documented dataset, metrics, bias/fairness testing, and regression checks.'}",
        "## Security Controls\nRequires prompt-injection, data leakage, access-control, and logging tests.",
        f"## Monitoring\n{profile.get('monitoring_status') or 'Monitoring approach must be documented before approval.'}",
        "## Incident Response\nIncident response workflow must be linked to AI incidents.",
        "## Audit Logging\nRecommendation and human decision logs should be retained under policy.",
        "## Data Retention\nRetention must be documented for source data, embeddings, prompts, and outputs.",
        "## Open Gaps\n" + "\n".join(f"- {gap['gap']}" for gap in gaps["critical_gaps"] + gaps["medium_gaps"]),
        "## Approval Status\nNeeds Review",
    ]
    state["ai_system_card"] = {
        "title": title,
        "content_markdown": "\n\n".join(markdown),
        "content_json": {"required_sections": SECTIONS},
        "status": "draft",
    }
    state.setdefault("tool_calls", []).append({"tool_name": "generate_ai_system_card", "status": "success"})
    return state
