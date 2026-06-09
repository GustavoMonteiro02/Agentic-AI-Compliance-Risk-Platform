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

tabs = st.tabs([
    "Dashboard",
    "AI System Intake",
    "Demo Scenarios",
    "Assessment",
    "Requirements",
    "Evidence",
    "System Card",
    "Audit Report",
    "Human Review",
    "Evaluation",
])

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
        technical_owner = st.text_input("Technical owner", value="AI Engineering Lead")
        deployment_status = st.selectbox("Deployment status", ["prototype", "internal", "production", "external"])
        users_affected = st.text_input("Users affected", value="job candidates")
        external_users_affected = st.checkbox("External users affected", value=True)
        data_types = st.text_input("Data types", value="CVs/resumes, embeddings, candidate fit scores")
        model_provider = st.text_input("Model provider", value="OpenAI")
        model_type = st.text_input("Model type", value="LLM-assisted workflow")
        decision_impact = st.selectbox("Decision impact", ["recommendation", "low", "medium", "high"])
        autonomy_level = st.selectbox("Level of autonomy", ["human-in-the-loop", "human-on-the-loop", "automated", "unknown"])
        integrations_tools_used = st.text_input("Integrations/tools used", value="ATS, vector database")
        monitoring_status = st.text_input("Monitoring status", value="Not yet documented")
        evaluation_status = st.text_input("Evaluation status", value="Evaluation dataset pending")
        security_testing_status = st.text_input("Security testing status", value="Prompt injection testing pending")
        human_oversight_process = st.text_area(
            "Human oversight process",
            value="Recruiters review AI rankings before any hiring decision.",
            height=80,
        )
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
                "technical_owner": technical_owner,
                "deployment_status": deployment_status,
                "users_affected": [item.strip() for item in users_affected.split(",") if item.strip()],
                "external_users_affected": external_users_affected,
                "data_types": [item.strip() for item in data_types.split(",") if item.strip()],
                "model_provider": model_provider,
                "model_type": model_type,
                "decision_impact": decision_impact,
                "autonomy_level": autonomy_level,
                "human_oversight_process": human_oversight_process,
                "integrations_tools_used": [
                    item.strip() for item in integrations_tools_used.split(",") if item.strip()
                ],
                "monitoring_status": monitoring_status,
                "evaluation_status": evaluation_status,
                "security_testing_status": security_testing_status,
            },
        )
        assessment = api_post(f"/systems/{system['id']}/assess")
        st.session_state["assessment_id"] = assessment["id"]
        st.success("Assessment generated and queued for human review.")

with tabs[2]:
    st.subheader("Demo Scenario Pack")
    scenarios = api_get("/demo/scenarios")
    st.dataframe(
        [
            {
                "Slug": item["slug"],
                "System": item["name"],
                "Business unit": item.get("business_unit"),
                "Deployment": item.get("deployment_status"),
            }
            for item in scenarios
        ],
        use_container_width=True,
    )
    if scenarios:
        selected_scenario = st.selectbox(
            "Scenario",
            options=scenarios,
            format_func=lambda item: item["name"],
        )
        st.write(selected_scenario["description"])
        if st.button("Create and assess scenario"):
            assessment = api_post(f"/demo/scenarios/{selected_scenario['slug']}/assess")
            st.session_state["assessment_id"] = assessment["id"]
            st.success("Demo assessment generated.")

assessment_id = st.session_state.get("assessment_id")
if not assessment_id:
    try:
        recent = api_get("/assessments")
        assessment_id = recent[0]["id"] if recent else None
    except Exception:
        assessment_id = None

assessment = api_get(f"/assessments/{assessment_id}") if assessment_id else None

with tabs[3]:
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

with tabs[4]:
    st.subheader("Requirement Knowledge Base")
    query = st.text_input("Search requirements", value="human oversight")
    requirements_path = f"/requirements?q={query}" if query else "/requirements"
    try:
        requirements = api_get(requirements_path)
        st.dataframe(requirements, use_container_width=True)
    except Exception as exc:
        st.error(str(exc))

with tabs[5]:
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

with tabs[6]:
    if assessment:
        col_md, col_pdf = st.columns(2)
        col_md.download_button(
            "Download Markdown",
            data=assessment["ai_system_card"]["content_markdown"],
            file_name=f"{assessment['profile']['system_name'].lower().replace(' ', '_')}_system_card.md",
        )
        col_pdf.link_button("Download PDF", f"{API_BASE_URL}/reports/{assessment['id']}/system-card.pdf")
        st.markdown(assessment["ai_system_card"]["content_markdown"])

with tabs[7]:
    if assessment:
        col_md, col_pdf = st.columns(2)
        col_md.download_button(
            "Download Markdown",
            data=assessment["audit_report"]["content_markdown"],
            file_name=f"{assessment['profile']['system_name'].lower().replace(' ', '_')}_audit_report.md",
        )
        col_pdf.link_button("Download PDF", f"{API_BASE_URL}/reports/{assessment['id']}.pdf")
        st.markdown(assessment["audit_report"]["content_markdown"])

with tabs[8]:
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

with tabs[9]:
    try:
        st.dataframe(api_get("/evaluation/results"), use_container_width=True)
    except Exception as exc:
        st.error(str(exc))
