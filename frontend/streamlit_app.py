import os
from datetime import date, datetime, time
from urllib.parse import quote

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("PLATFORM_API_KEY")
API_USER = os.getenv("PLATFORM_USER", "streamlit-user")
API_USER_ROLE = os.getenv("PLATFORM_USER_ROLE", "admin")
API_TENANT_ID = os.getenv("PLATFORM_TENANT_ID", "default")

st.set_page_config(page_title="AI Governance Platform", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.25rem; padding-bottom: 2rem; max-width: 1280px;}
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e4e7ec;
        border-radius: 8px;
        padding: 14px 16px;
        min-height: 104px;
    }
    div[data-testid="stDataFrame"] {border: 1px solid #e4e7ec; border-radius: 8px;}
    .section-title {font-size: 1.15rem; font-weight: 700; margin: 0.5rem 0 0.75rem 0;}
    .muted {color: #667085; font-size: 0.92rem;}
    .status-pill {
        display: inline-block;
        padding: 0.18rem 0.55rem;
        border-radius: 999px;
        background: #eef4ff;
        color: #3538cd;
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_headers() -> dict[str, str]:
    headers = {"X-User": API_USER, "X-User-Role": API_USER_ROLE, "X-Tenant-ID": API_TENANT_ID}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    return headers


def api_get(path: str):
    response = requests.get(f"{API_BASE_URL}{path}", headers=api_headers(), timeout=30)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    return response.json() if content_type.startswith("application/json") else response.text


def api_post(path: str, payload: dict | None = None):
    response = requests.post(f"{API_BASE_URL}{path}", json=payload or {}, headers=api_headers(), timeout=90)
    response.raise_for_status()
    return response.json()


def api_patch(path: str, payload: dict):
    response = requests.patch(f"{API_BASE_URL}{path}", json=payload, headers=api_headers(), timeout=30)
    response.raise_for_status()
    return response.json()


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def risk_label(level: str) -> str:
    return {
        "high": "High",
        "medium": "Medium",
        "limited": "Limited",
        "minimal": "Minimal",
        "unknown": "Unknown",
        "unacceptable": "Unacceptable",
    }.get(level, level.title())


def parse_api_date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def date_to_api_datetime(value: date | None) -> str | None:
    if value is None:
        return None
    return datetime.combine(value, time(hour=12)).isoformat()


def current_assessment():
    assessment_id = st.session_state.get("assessment_id")
    if not assessment_id:
        try:
            recent = api_get("/assessments")
            assessment_id = recent[0]["id"] if recent else None
        except Exception:
            assessment_id = None
    return api_get(f"/assessments/{assessment_id}") if assessment_id else None


def page_header(title: str, subtitle: str):
    st.title(title)
    st.markdown(f"<div class='muted'>{subtitle}</div>", unsafe_allow_html=True)


def show_assessment_picker():
    try:
        assessments = api_get("/assessments")
    except Exception:
        return
    if not assessments:
        return
    selected = st.sidebar.selectbox(
        "Active assessment",
        assessments,
        format_func=lambda item: f"{item['profile']['system_name']} - {item['status']}",
    )
    if selected:
        st.session_state["assessment_id"] = selected["id"]


def runtime_llm_options() -> dict:
    try:
        return api_get("/runtime/llm-options")
    except Exception:
        return {
            "default_mode": "deterministic",
            "default_provider": None,
            "default_model": None,
            "providers": [],
            "defaults": {"timeout_seconds": 60, "max_retries": 2, "max_tokens": 2000, "temperature": 0.1},
        }


def llm_config_controls(key_prefix: str = "assessment") -> dict:
    options = runtime_llm_options()
    providers = options.get("providers", [])
    defaults = options.get("defaults", {})

    st.markdown("<div class='section-title'>Assessment runtime</div>", unsafe_allow_html=True)
    mode_choices = ["deterministic"]
    if providers:
        mode_choices.append("llm")
    default_mode = "llm" if providers and options.get("default_mode") in {"llm", "openai"} else "deterministic"
    mode = st.selectbox(
        "Generation mode",
        mode_choices,
        index=mode_choices.index(default_mode),
        key=f"{key_prefix}_generation_mode",
    )

    if mode == "deterministic":
        if not providers:
            st.caption("No live LLM provider is configured. Add a provider key in .env to enable LLM mode.")
        return {"ai_generation_mode": "deterministic"}

    provider_ids = [item["id"] for item in providers]
    default_provider = options.get("default_provider") if options.get("default_provider") in provider_ids else provider_ids[0]
    provider = st.selectbox(
        "LLM provider",
        providers,
        index=provider_ids.index(default_provider),
        format_func=lambda item: f"{item['label']} - {item['model']}",
        key=f"{key_prefix}_llm_provider",
    )
    model = st.text_input("Model", value=provider.get("model") or options.get("default_model") or "", key=f"{key_prefix}_model")
    cols = st.columns(4)
    max_tokens = cols[0].number_input(
        "Max tokens",
        min_value=128,
        max_value=8000,
        value=int(defaults.get("max_tokens") or 2000),
        step=128,
        key=f"{key_prefix}_max_tokens",
    )
    timeout_seconds = cols[1].number_input(
        "Timeout seconds",
        min_value=1,
        max_value=300,
        value=int(defaults.get("timeout_seconds") or 60),
        step=5,
        key=f"{key_prefix}_timeout",
    )
    max_retries = cols[2].number_input(
        "Retries",
        min_value=0,
        max_value=5,
        value=int(defaults.get("max_retries") or 0),
        step=1,
        key=f"{key_prefix}_retries",
    )
    temperature = cols[3].number_input(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=float(defaults.get("temperature") if defaults.get("temperature") is not None else 0.1),
        step=0.05,
        key=f"{key_prefix}_temperature",
    )
    return {
        "ai_generation_mode": "llm",
        "llm_provider": provider["id"],
        "model": model.strip() or provider.get("model"),
        "max_tokens": int(max_tokens),
        "timeout_seconds": int(timeout_seconds),
        "max_retries": int(max_retries),
        "temperature": float(temperature),
    }


st.sidebar.title("AI Governance")
try:
    runtime = api_get("/runtime/status")
    st.sidebar.caption(
        f"Mode: {runtime['ai_generation_mode']} | LLM: {'on' if runtime['llm_enabled'] else 'off'} | Vector: {runtime['vector_db']}"
    )
except Exception:
    st.sidebar.caption("Runtime status unavailable")
page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Intake",
        "Demo Scenarios",
        "Assessment",
        "Requirements",
        "Evidence",
        "Risk Register",
        "System Card",
        "Audit Report",
        "Human Review",
        "Evaluation",
    ],
)
st.sidebar.caption(f"API: {API_BASE_URL}")
show_assessment_picker()

assessment = current_assessment()

if page == "Dashboard":
    page_header("Governance Dashboard", "Portfolio-grade overview for AI systems, reviews, evidence and readiness.")
    systems = api_get("/systems")
    assessments = api_get("/assessments")
    high_risk = [item for item in assessments if item["risk_classification"]["risk_level"] == "high"]
    approved = [item for item in assessments if item["human_review_status"] == "approved"]
    rejected = [item for item in assessments if item["human_review_status"] == "rejected"]
    pending = [item for item in assessments if item["human_review_status"] == "needs_review"]
    missing_evidence = sum(
        1 for item in assessments for evidence in item["evidence_checklist"] if evidence["status"] == "missing"
    )
    readiness_scores = []
    for item in assessments:
        try:
            readiness_scores.append(api_get(f"/evidence/assessments/{item['id']}/readiness-score")["score"])
        except Exception:
            readiness_scores.append(0)
    average_readiness = sum(readiness_scores) / len(readiness_scores) if readiness_scores else 0

    cols = st.columns(6)
    cols[0].metric("AI systems", len(systems))
    cols[1].metric("High risk", len(high_risk))
    cols[2].metric("Pending", len(pending))
    cols[3].metric("Approved", len(approved))
    cols[4].metric("Rejected", len(rejected))
    cols[5].metric("Readiness", f"{average_readiness:.0f}%")
    st.metric("Missing evidence items", missing_evidence)

    if assessments:
        st.markdown("<div class='section-title'>Recent assessments</div>", unsafe_allow_html=True)
        st.dataframe(
            [
                {
                    "System": item["profile"]["system_name"],
                    "Risk": risk_label(item["risk_classification"]["risk_level"]),
                    "Review": item["human_review_status"],
                    "Critical gaps": len(item["gap_analysis"]["critical_gaps"]),
                    "Evidence": len(item["evidence_checklist"]),
                }
                for item in assessments[:15]
            ],
            hide_index=True,
            use_container_width=True,
            height=420,
        )

elif page == "Intake":
    page_header("AI System Intake", "Register a system with structured governance fields and run an assessment.")
    with st.form("system_form"):
        left, right = st.columns(2)
        with left:
            name = st.text_input("System name", value="Recruitment CV Screening Assistant")
            business_unit = st.text_input("Business unit", value="People Operations")
            owner = st.text_input("System owner", value="Head of Talent")
            technical_owner = st.text_input("Technical owner", value="AI Engineering Lead")
            deployment_status = st.selectbox("Deployment status", ["prototype", "internal", "production", "external"])
            users_affected = st.text_input("Users affected", value="job candidates")
            external_users_affected = st.checkbox("External users affected", value=True)
        with right:
            data_types = st.text_input("Data types", value="CVs/resumes, embeddings, candidate fit scores")
            model_provider = st.text_input("Model provider", value="OpenAI")
            model_type = st.text_input("Model type", value="LLM-assisted workflow")
            decision_impact = st.selectbox("Decision impact", ["recommendation", "low", "medium", "high"])
            autonomy_level = st.selectbox(
                "Level of autonomy", ["human-in-the-loop", "human-on-the-loop", "automated", "unknown"]
            )
            integrations_tools_used = st.text_input("Integrations/tools used", value="ATS, vector database")

        status_cols = st.columns(3)
        monitoring_status = status_cols[0].text_input("Monitoring status", value="Not yet documented")
        evaluation_status = status_cols[1].text_input("Evaluation status", value="Evaluation dataset pending")
        security_testing_status = status_cols[2].text_input("Security testing status", value="Prompt injection testing pending")
        human_oversight_process = st.text_area(
            "Human oversight process",
            value="Recruiters review AI rankings before any hiring decision.",
            height=90,
        )
        description = st.text_area(
            "Use case description",
            value=(
                "We use an AI assistant in HR to analyze CVs, rank candidates and generate "
                "recommendations for recruiters. The system processes personal data, stores "
                "embeddings of CVs and produces candidate fit scores. Final hiring decisions are reviewed by humans."
            ),
            height=150,
        )
        llm_config = llm_config_controls("intake")
        submitted = st.form_submit_button("Create and assess", use_container_width=True)
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
                "users_affected": split_csv(users_affected),
                "external_users_affected": external_users_affected,
                "data_types": split_csv(data_types),
                "model_provider": model_provider,
                "model_type": model_type,
                "decision_impact": decision_impact,
                "autonomy_level": autonomy_level,
                "human_oversight_process": human_oversight_process,
                "integrations_tools_used": split_csv(integrations_tools_used),
                "monitoring_status": monitoring_status,
                "evaluation_status": evaluation_status,
                "security_testing_status": security_testing_status,
            },
        )
        result = api_post(f"/systems/{system['id']}/assess", {"llm_config": llm_config})
        st.session_state["assessment_id"] = result["id"]
        st.success("Assessment generated and queued for human review.")

elif page == "Demo Scenarios":
    page_header("Demo Scenario Pack", "One-click assessments for portfolio walkthroughs.")
    scenarios = api_get("/demo/scenarios")
    st.dataframe(
        [
            {
                "Scenario": item["name"],
                "Business unit": item.get("business_unit"),
                "Deployment": item.get("deployment_status"),
                "Slug": item["slug"],
            }
            for item in scenarios
        ],
        hide_index=True,
        use_container_width=True,
        height=260,
    )
    selected = st.selectbox("Scenario", scenarios, format_func=lambda item: item["name"])
    st.info(selected["description"])
    llm_config = llm_config_controls("demo")
    if st.button("Create and assess scenario", use_container_width=True):
        result = api_post(f"/demo/scenarios/{selected['slug']}/assess", {"llm_config": llm_config})
        st.session_state["assessment_id"] = result["id"]
        st.success("Demo assessment generated.")

elif page == "Assessment":
    page_header("Risk Assessment", "Risk, grounded requirements, controls, gaps and recommended actions.")
    if not assessment:
        st.info("Create or select an assessment first.")
    else:
        risk = assessment["risk_classification"]
        cols = st.columns(4)
        cols[0].metric("Risk level", risk_label(risk["risk_level"]))
        cols[1].metric("Confidence", f"{risk['confidence']:.0%}")
        cols[2].metric("Critical gaps", len(assessment["gap_analysis"]["critical_gaps"]))
        cols[3].metric("Review status", assessment["human_review_status"])
        st.markdown(f"<span class='status-pill'>{assessment['disclaimer']}</span>", unsafe_allow_html=True)
        st.write(risk["reasoning_summary"])
        with st.expander("Risk factors", expanded=True):
            st.write(risk["risk_factors"])
        with st.expander("Relevant requirements", expanded=True):
            requirement_rows = [
                {
                    "Requirement": item["title"],
                    "Source": item["source"],
                    "Type": item.get("document_type"),
                    "Jurisdiction": item.get("jurisdiction"),
                    "Relevance": item.get("relevance"),
                    "Score": item.get("score"),
                }
                for item in assessment["retrieved_requirements"]
            ]
            st.dataframe(requirement_rows, hide_index=True, use_container_width=True, height=300)
        with st.expander("Mapped controls", expanded=True):
            st.dataframe(assessment["mapped_controls"], hide_index=True, use_container_width=True, height=300)
        with st.expander("Gap analysis", expanded=True):
            st.json(assessment["gap_analysis"], expanded=False)

elif page == "Requirements":
    page_header("Requirement Knowledge Base", "Search seeded policy, control and regulation requirements.")
    query = st.text_input("Search requirements", value="human oversight")
    requirements_path = f"/requirements?q={quote(query)}" if query else "/requirements"
    requirements = api_get(requirements_path)
    st.dataframe(requirements, hide_index=True, use_container_width=True, height=560)

elif page == "Evidence":
    page_header("Evidence Center", "Track evidence status, owners, links and readiness.")
    if not assessment:
        st.info("Create or select an assessment first.")
    else:
        readiness = api_get(f"/evidence/assessments/{assessment['id']}/readiness-score")
        cols = st.columns(6)
        cols[0].metric("Readiness", f"{readiness['score']:.1f}%")
        cols[1].metric("Approved", readiness["approved"])
        cols[2].metric("Missing", readiness["missing"])
        cols[3].metric("Overdue", readiness.get("overdue", 0))
        cols[4].metric("Expired", readiness.get("expired", 0))
        cols[5].metric("Retention due", readiness.get("retention_due", 0))
        evidence_records = api_get(f"/evidence/assessments/{assessment['id']}")
        st.dataframe(
            [
                {
                    "Evidence": item["name"],
                    "Status": item["status"],
                    "Priority": item["priority"],
                    "Owner": item["owner"],
                    "Due": item.get("due_date"),
                    "Expires": item.get("expires_at"),
                    "Source": item.get("source_system"),
                    "Collected": item.get("collected_at"),
                    "Approved by": item.get("approved_by"),
                }
                for item in evidence_records
            ],
            hide_index=True,
            use_container_width=True,
            height=360,
        )
        selected = st.selectbox("Evidence item", evidence_records, format_func=lambda item: f"{item['name']} - {item['status']}")
        edit_cols = st.columns(3)
        new_status = edit_cols[0].selectbox(
            "Status",
            ["missing", "partial", "generated", "uploaded", "approved", "rejected"],
            index=["missing", "partial", "generated", "uploaded", "approved", "rejected"].index(selected["status"]),
        )
        owner = edit_cols[1].text_input("Owner", value=selected["owner"])
        approved_by = edit_cols[2].text_input("Approved by", value=selected.get("approved_by") or "")
        file_url = st.text_input("Evidence URL", value=selected.get("file_url") or "")
        source_cols = st.columns(2)
        source_system = source_cols[0].text_input("Source system", value=selected.get("source_system") or "")
        evidence_hash = source_cols[1].text_input("Checksum / hash", value=selected.get("evidence_hash") or "")
        date_cols = st.columns(4)
        due_date = date_cols[0].date_input("Due date", value=parse_api_date(selected.get("due_date")))
        expires_at = date_cols[1].date_input("Expires at", value=parse_api_date(selected.get("expires_at")))
        collected_at = date_cols[2].date_input("Collected at", value=parse_api_date(selected.get("collected_at")))
        retention_until = date_cols[3].date_input("Retention until", value=parse_api_date(selected.get("retention_until")))
        description = st.text_area("Evidence notes", value=selected.get("description") or "", height=90)
        review_notes = st.text_area("Review notes", value=selected.get("review_notes") or "", height=80)
        if st.button("Update evidence", use_container_width=True):
            api_patch(
                f"/evidence/items/{selected['id']}",
                {
                    "status": new_status,
                    "owner": owner,
                    "description": description,
                    "file_url": file_url or None,
                    "source_system": source_system or None,
                    "evidence_hash": evidence_hash or None,
                    "collected_at": date_to_api_datetime(collected_at),
                    "retention_until": date_to_api_datetime(retention_until),
                    "due_date": date_to_api_datetime(due_date),
                    "expires_at": date_to_api_datetime(expires_at),
                    "approved_by": approved_by or None,
                    "review_notes": review_notes or None,
                },
            )
            st.success("Evidence updated.")

elif page == "Risk Register":
    page_header("Risk Register", "Track residual risks, mitigation plans and policy exceptions.")
    if assessment and st.button("Sync risks from active assessment", use_container_width=True):
        api_post(f"/risk-register/assessments/{assessment['id']}/sync")
        st.success("Risk register synced.")
    risks = api_get("/risk-register")
    st.dataframe(
        [
            {
                "Title": item["title"],
                "Severity": item["severity"],
                "Status": item["status"],
                "Owner": item["owner"],
                "Due": item.get("due_date"),
                "Mitigation": item.get("mitigation_plan"),
            }
            for item in risks
        ],
        hide_index=True,
        use_container_width=True,
        height=300,
    )
    if risks:
        selected_risk = st.selectbox("Risk item", risks, format_func=lambda item: f"{item['title']} - {item['status']}")
        risk_cols = st.columns(3)
        risk_status = risk_cols[0].selectbox("Risk status", ["open", "mitigating", "accepted", "closed"], index=["open", "mitigating", "accepted", "closed"].index(selected_risk["status"]))
        risk_owner = risk_cols[1].text_input("Risk owner", value=selected_risk["owner"])
        risk_due = risk_cols[2].date_input("Risk due date", value=parse_api_date(selected_risk.get("due_date")))
        mitigation_plan = st.text_area("Mitigation plan", value=selected_risk.get("mitigation_plan") or "", height=90)
        if st.button("Update risk", use_container_width=True):
            api_patch(
                f"/risk-register/{selected_risk['id']}",
                {
                    "status": risk_status,
                    "owner": risk_owner,
                    "due_date": date_to_api_datetime(risk_due),
                    "mitigation_plan": mitigation_plan,
                },
            )
            st.success("Risk updated.")

    st.markdown("<div class='section-title'>Policy exceptions</div>", unsafe_allow_html=True)
    exceptions = api_get("/risk-register/exceptions")
    st.dataframe(
        [
            {
                "Title": item["title"],
                "Status": item["status"],
                "Requested by": item["requested_by"],
                "Approved by": item.get("approved_by"),
                "Expires": item.get("expires_at"),
            }
            for item in exceptions
        ],
        hide_index=True,
        use_container_width=True,
        height=220,
    )
    with st.form("policy_exception_form"):
        if not assessment:
            st.info("Select an assessment before requesting an exception.")
        exception_title = st.text_input("Exception title", value="Temporary compensating control exception")
        requirement_id = st.text_input("Requirement ID", value="")
        requested_by = st.text_input("Requested by", value=API_USER)
        justification = st.text_area("Justification", value="Temporary exception while the control is implemented.", height=90)
        compensating_controls = st.text_input("Compensating controls", value="Manual review, weekly monitoring")
        expires_at = st.date_input("Exception expiry", value=None)
        if st.form_submit_button("Request exception", use_container_width=True) and assessment:
            api_post(
                "/risk-register/exceptions",
                {
                    "assessment_id": assessment["id"],
                    "requirement_id": requirement_id or None,
                    "title": exception_title,
                    "justification": justification,
                    "compensating_controls": split_csv(compensating_controls),
                    "requested_by": requested_by,
                    "expires_at": date_to_api_datetime(expires_at),
                },
            )
            st.success("Exception requested.")

elif page == "System Card":
    page_header("AI System Card", "Generated system documentation for human review.")
    if not assessment:
        st.info("Create or select an assessment first.")
    else:
        col_md, col_pdf = st.columns(2)
        col_md.download_button(
            "Download Markdown",
            data=assessment["ai_system_card"]["content_markdown"],
            file_name=f"{assessment['profile']['system_name'].lower().replace(' ', '_')}_system_card.md",
            use_container_width=True,
        )
        col_pdf.link_button("Download PDF", f"{API_BASE_URL}/reports/{assessment['id']}/system-card.pdf", use_container_width=True)
        st.markdown(assessment["ai_system_card"]["content_markdown"])

elif page == "Audit Report":
    page_header("Audit Report", "Audit-readiness report with gaps, controls and evidence.")
    if not assessment:
        st.info("Create or select an assessment first.")
    else:
        col_md, col_pdf = st.columns(2)
        col_md.download_button(
            "Download Markdown",
            data=assessment["audit_report"]["content_markdown"],
            file_name=f"{assessment['profile']['system_name'].lower().replace(' ', '_')}_audit_report.md",
            use_container_width=True,
        )
        col_pdf.link_button("Download PDF", f"{API_BASE_URL}/reports/{assessment['id']}.pdf", use_container_width=True)
        st.markdown(assessment["audit_report"]["content_markdown"])

elif page == "Human Review":
    page_header("Human Review", "Review queue, status decisions, notes and history.")
    if not assessment:
        st.info("Create or select an assessment first.")
    else:
        st.dataframe(api_get("/reviews/queue"), hide_index=True, use_container_width=True, height=280)
        st.markdown(f"Current status: `{assessment['human_review_status']}`")
        reviewer = st.text_input("Reviewer", value="Compliance Reviewer")
        notes = st.text_area("Reviewer notes", value="Reviewed as draft. Evidence gaps must be tracked.", height=100)
        col1, col2, col3 = st.columns(3)
        if col1.button("Approve", use_container_width=True):
            st.success(api_post(f"/reviews/{assessment['id']}/approve", {"reviewer": reviewer, "notes": notes})["status"])
        if col2.button("Reject", use_container_width=True):
            st.warning(api_post(f"/reviews/{assessment['id']}/reject", {"reviewer": reviewer, "notes": notes})["status"])
        if col3.button("Request evidence", use_container_width=True):
            st.info(api_post(f"/reviews/{assessment['id']}/request-more-evidence", {"reviewer": reviewer, "notes": notes})["status"])
        st.dataframe(api_get(f"/reviews/{assessment['id']}/history"), hide_index=True, use_container_width=True, height=220)

elif page == "Evaluation":
    page_header("Evaluation Dashboard", "Guardrail, retrieval, structure and workflow metrics.")
    st.dataframe(api_get("/evaluation/results"), hide_index=True, use_container_width=True, height=520)
