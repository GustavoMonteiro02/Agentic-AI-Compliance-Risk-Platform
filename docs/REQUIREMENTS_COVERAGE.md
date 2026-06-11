# Requirements Coverage

This document maps the original project requirements to the current implementation.

## Implemented

- Local Git repository with milestone commits.
- Professional README, architecture, roadmap, and portfolio positioning.
- FastAPI backend with health, systems, assessments, reports, evidence, requirements, reviews, incidents, and evaluation routes.
- SQLAlchemy persistence compatible with SQLite for local development and PostgreSQL through Docker Compose.
- AI system inventory fields for owner, technical owner, business unit, deployment status, affected users, external users, data types, model provider, model type, decision impact, autonomy, human oversight, integrations/tools, monitoring status, evaluation status, and security testing status.
- Structured intake agent with adaptive missing-information questions.
- Follow-up answers accepted through `POST /systems/{system_id}/assess`.
- LangGraph-compiled governance workflow with intake, missing-info check, risk classification, regulatory retrieval, control mapping, gap analysis, evidence generation, system card generation, audit report generation, and human review gate.
- Local RAG knowledge base with policies, controls, source-linked regulation summaries, section metadata, citation payloads, hybrid retrieval, optional Qdrant vector scores, and reranking.
- Legal-source manifest and article-level ingestion path with locators and content hashes for official corpus expansion.
- Requirements seeding into the `requirements` database table from Markdown knowledge-base documents.
- Requirement search API and Streamlit Requirements tab.
- MCP tool, resource, and prompt catalog with tests.
- Evidence checklist records, evidence status updates, owners, due dates, expiry, approval metadata, and compliance readiness score.
- Remediation plan endpoint generated from critical gaps, medium gaps, missing evidence, owners, priorities, and due dates.
- Risk register and policy exception workflows with mitigation plans and compensating controls.
- AI incident lifecycle for reporting, triage, containment, resolution, corrective actions, regulatory report review, tenant scoping, and audit events.
- AI system card and audit report Markdown generation/export.
- Dedicated Pydantic schema modules for risk, controls, requirements, evidence, review, report, system, and assessment contracts.
- Human review queue, approve/reject/request-more-evidence actions, reviewer notes, risk override validation, and review history.
- Structured audit events for evidence updates and human review decisions.
- Tenant-scoped systems, assessments, evidence, reports, review queues, and audit events.
- Streamlit UI for dashboard, intake, assessment, requirements, evidence, system card, audit report, review, and evaluation.
- React SaaS UI scaffold for a production-style governance command center.
- Evaluation suite covering risk classification consistency, retrieval grounding, retrieval quality top-k recall, system card coverage, evidence completeness, human approval bypass resistance, legal-advice guardrails, and LangSmith-compatible experiment payloads.
- Guardrails preventing automatic approval or final legal compliance claims without human review.
- Dockerfile, Docker Compose, Makefile, CI workflow, security/configuration scan, runtime readiness checks, Docker healthchecks, and pytest suite.
- Optional OpenAI LLM refinement mode, LangSmith run metadata, Qdrant Docker service, and PDF report export.

## Intentionally Deferred External Integrations

These are represented by stable interfaces and roadmap entries, but are not enabled by default because the local MVP is designed to run without cloud credentials:

- Full LangChain provider abstraction across multiple LLM vendors.
- Pinecone as an alternative persistent vector database.
- Full official legal/regulatory corpora ingestion.

## Current Verification

- Test suite: run with `pytest`.
- Local API: `http://127.0.0.1:8000`.
- Local UI: `http://127.0.0.1:8501`.
