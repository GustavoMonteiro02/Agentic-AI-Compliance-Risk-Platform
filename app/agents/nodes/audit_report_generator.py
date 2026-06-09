from app.agents.state import GovernanceAssessmentState


def audit_report_generator_node(state: GovernanceAssessmentState) -> GovernanceAssessmentState:
    profile = state["system_profile"]
    risk = state["risk_classification"]
    gaps = state["gap_analysis"]
    evidence = state["evidence_checklist"]
    title = f"Audit Readiness Report: {profile['system_name']}"

    requirement_lines = [
        f"- {req['requirement_id']}: {req['title']} ({req['source']})"
        for req in state.get("retrieved_requirements", [])
    ]
    evidence_lines = [f"- {item['evidence']}: {item['status']} / {item['priority']}" for item in evidence]
    action_lines = [f"- {action}" for action in gaps.get("priority_actions", [])]

    markdown = f"""# {title}

> Draft audit-readiness report for human review. This is not legal advice.

## Executive Summary

The system is preliminarily classified as **{risk['risk_level']}** risk. The assessment requires human review before any compliance conclusion is made.

## System Overview

{profile['use_case']}

Business unit: {profile.get('business_unit') or 'Not specified'}
Owner: {profile.get('system_owner') or 'Not specified'}
Deployment status: {profile.get('deployment_status') or 'Unknown'}

## Key Risk Factors

{chr(10).join(f"- {factor}" for factor in risk['risk_factors'])}

## Relevant Requirements

{chr(10).join(requirement_lines)}

## Gap Analysis

Critical gaps: {len(gaps['critical_gaps'])}
Medium gaps: {len(gaps['medium_gaps'])}

## Evidence Checklist

{chr(10).join(evidence_lines)}

## Recommended Remediation Plan

{chr(10).join(action_lines)}

## Human Review Status

Needs Review
"""
    state["audit_report"] = {
        "title": title,
        "content_markdown": markdown,
        "content_json": {"critical_gap_count": len(gaps["critical_gaps"])},
        "status": "draft",
    }
    state.setdefault("tool_calls", []).append({"tool_name": "generate_audit_report", "status": "success"})
    return state
