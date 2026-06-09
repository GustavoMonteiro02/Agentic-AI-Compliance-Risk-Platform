import os

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="AI Governance Platform", layout="wide")


def api_get(path: str):
    response = requests.get(f"{API_BASE_URL}{path}", timeout=20)
    response.raise_for_status()
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text


def api_post(path: str, payload: dict | None = None):
    response = requests.post(f"{API_BASE_URL}{path}", json=payload or {}, timeout=60)
    response.raise_for_status()
    return response.json()


def api_patch(path: str, payload: dict):
    response = requests.patch(f"{API_BASE_URL}{path}", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def risk_badge(level: str) -> str:
    return {
        "high": "High",
        "medium": "Medium",
        "limited": "Limited",
        "minimal": "Minimal",
        "unknown": "Unknown",
    }.get(level, level.title())


st.title("AI Governance & Compliance Intelligence Platform")

tabs = st.tabs(["Dashboard", "AI System Intake", "Assessment", "Evidence", "System Card", "Audit Report", "Human Review", "Evaluation"])

with tabs[0]:
    systems = api_get("/systems")
    assessments = api_get("/assessments")
    high_risk = [item for item in assessments if item["risk_classification"]["risk_level"] == "high"]
    pending = [item for item in assessments if item["human_review_status"] == "needs_review"]
    missing_evidence = sum(
        1 for assessment in assessments for item in assessment["evidence_checklist"] if item["status"] == "missing"
    )
    readiness_scores = []
    for item in assessments:
        try:
            readiness_scores.append(api_get(f"/evidence/assessments/{item['id']}/readiness-score")["score"])
        except Exception:
            readiness_scores.append(0)
    average_readiness = sum(readiness_scores) / len(readiness_scores) if readiness_scores else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total AI systems", len(systems))
    col2.metric("High-risk systems", len(high_risk))
    col3.metric("Pending reviews", len(pending))
    col4.metric("Missing evidence", missing_evidence)
    col5.metric("Avg readiness", f"{average_readiness:.0f}%")

    if assessments:
        st.dataframe(
            [
                {
                    "System": item["profile"]["system_name"],
                    "Risk": risk_badge(item["risk_classification"]["risk_level"]),
                    "Status": item["status"],
                    "Evidence items": len(item["evidence_checklist"]),
                }
                for item in assessments
            ],
            use_container_width=True,
        )

with tabs[1]:
    st.subheader("Register AI System")
    with st.form("system_form"):
        name = st.text_input("System name", value="Recruitment CV Screening Assistant")
        business_unit = st.text_input("Business unit", value="People Operations")
        owner = st.text_input("Owner", value="Head of Talent")
        description = st.text_area(
            "Use case description",
            value=(
                "We use an AI assistant in HR to analyze CVs, rank candidates and generate "
                "recommendations for recruiters. The system processes personal data, stores "
                "embeddings of CVs and produces candidate fit scores. Final hiring decisions "
                "are reviewed by humans."
            ),
            height=160,
        )
        submitted = st.form_submit_button("Create and assess")
    if submitted:
        system = api_post(
            "/systems",
            {
                "name": name,
                "description": description,
                "business_unit": business_unit,
                "owner": owner,
                "deployment_status": "prototype",
            },
        )
        assessment = api_post(f"/systems/{system['id']}/assess")
        st.session_state["assessment_id"] = assessment["id"]
        st.success("Assessment generated and queued for human review.")

assessment_id = st.session_state.get("assessment_id")
if not assessment_id:
    try:
        recent = api_get("/assessments")
        assessment_id = recent[0]["id"] if recent else None
    except Exception:
        assessment_id = None

assessment = api_get(f"/assessments/{assessment_id}") if assessment_id else None

with tabs[2]:
    if assessment:
        risk = assessment["risk_classification"]
        st.metric("Risk level", risk_badge(risk["risk_level"]), f"{risk['confidence']:.0%} confidence")
        st.write(risk["reasoning_summary"])
        st.subheader("Risk factors")
        st.write(risk["risk_factors"])
        st.subheader("Relevant requirements")
        st.dataframe(assessment["retrieved_requirements"], use_container_width=True)
        st.subheader("Mapped controls")
        st.dataframe(assessment["mapped_controls"], use_container_width=True)
        st.subheader("Gaps")
        st.json(assessment["gap_analysis"])
    else:
        st.info("Create an AI system to view an assessment.")

with tabs[3]:
    if assessment:
        readiness = api_get(f"/evidence/assessments/{assessment['id']}/readiness-score")
        st.metric("Compliance readiness score", f"{readiness['score']:.1f}%")
        evidence_records = api_get(f"/evidence/assessments/{assessment['id']}")
        st.dataframe(evidence_records, use_container_width=True)
        if evidence_records:
            selected = st.selectbox(
                "Evidence item",
                options=evidence_records,
                format_func=lambda item: f"{item['name']} ({item['status']})",
            )
            new_status = st.selectbox(
                "Status",
                ["missing", "partial", "generated", "uploaded", "approved", "rejected"],
                index=["missing", "partial", "generated", "uploaded", "approved", "rejected"].index(selected["status"]),
            )
            description = st.text_area("Evidence notes", value=selected.get("description") or "")
            file_url = st.text_input("Evidence URL", value=selected.get("file_url") or "")
            if st.button("Update evidence"):
                api_patch(
                    f"/evidence/items/{selected['id']}",
                    {"status": new_status, "description": description, "file_url": file_url or None},
                )
                st.success("Evidence updated.")

with tabs[4]:
    if assessment:
        st.download_button(
            "Download system card markdown",
            data=assessment["ai_system_card"]["content_markdown"],
            file_name=f"{assessment['profile']['system_name'].lower().replace(' ', '_')}_system_card.md",
        )
        st.markdown(assessment["ai_system_card"]["content_markdown"])

with tabs[5]:
    if assessment:
        st.download_button(
            "Download audit report markdown",
            data=assessment["audit_report"]["content_markdown"],
            file_name=f"{assessment['profile']['system_name'].lower().replace(' ', '_')}_audit_report.md",
        )
        st.markdown(assessment["audit_report"]["content_markdown"])

with tabs[6]:
    if assessment:
        st.subheader("Review queue")
        try:
            st.dataframe(api_get("/reviews/queue"), use_container_width=True)
        except Exception as exc:
            st.warning(str(exc))
        st.write(f"Current status: `{assessment['human_review_status']}`")
        reviewer = st.text_input("Reviewer", value="Compliance Reviewer")
        notes = st.text_area("Reviewer notes", value="Reviewed as draft. Evidence gaps must be tracked.")
        col1, col2, col3 = st.columns(3)
        if col1.button("Approve"):
            result = api_post(f"/reviews/{assessment['id']}/approve", {"reviewer": reviewer, "notes": notes})
            st.success(f"Assessment {result['status']}")
        if col2.button("Reject"):
            result = api_post(f"/reviews/{assessment['id']}/reject", {"reviewer": reviewer, "notes": notes})
            st.warning(f"Assessment {result['status']}")
        if col3.button("Request more evidence"):
            result = api_post(
                f"/reviews/{assessment['id']}/request-more-evidence", {"reviewer": reviewer, "notes": notes}
            )
            st.info(f"Assessment {result['status']}")
        st.subheader("Review history")
        st.dataframe(api_get(f"/reviews/{assessment['id']}/history"), use_container_width=True)

with tabs[7]:
    try:
        st.dataframe(api_get("/evaluation/results"), use_container_width=True)
    except Exception as exc:
        st.error(str(exc))
