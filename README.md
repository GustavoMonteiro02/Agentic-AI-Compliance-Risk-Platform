# AI Governance & Compliance Intelligence Platform

A production-oriented agentic AI governance platform that classifies AI system risk, maps regulatory and internal policy requirements to controls, identifies compliance gaps, generates evidence checklists, and produces audit-ready AI system cards using LangGraph-style orchestration, RAG, MCP, FastAPI, PostgreSQL, and a React product UI.

> This project supports governance, risk, compliance, and audit preparation. It does not provide legal advice and never marks an AI system as compliant without human review.

## Problem

Organizations are adopting AI systems faster than governance, compliance, security, and audit teams can document them. Teams need a practical workflow to inventory systems, classify risk, identify missing controls, gather evidence, and prepare structured documentation for review.

This platform demonstrates how an AI Engineer / Agentic AI Engineer can build agentic workflows for a real enterprise problem beyond simple chatbots or basic RAG demos.

## Architecture

```mermaid
flowchart LR
    UI["React UI"] --> API["FastAPI API"]
    API --> DB["PostgreSQL or SQLite dev DB"]
    API --> Graph["Governance LangGraph Workflow"]
    Graph --> Intake["Intake Agent"]
    Graph --> Risk["Risk Classification Agent"]
    Graph --> RAG["Regulatory RAG Agent"]
    RAG --> KB["Markdown Knowledge Base"]
    Graph --> Controls["Control Mapping Agent"]
    Graph --> Gaps["Gap Analysis Agent"]
    Graph --> Evidence["Evidence Checklist Agent"]
    Graph --> Card["AI System Card Generator"]
    Graph --> Report["Audit Report Generator"]
    Graph --> Review["Human Review Node"]
    API --> MCP["MCP Compliance Server"]
```

The MVP is intentionally deterministic by default so it can run locally without API keys. The agent nodes are designed to be upgraded with LangChain model calls and LangSmith tracing through the same interfaces.

See [Requirements Coverage](docs/REQUIREMENTS_COVERAGE.md) for a mapping from the original project brief to the current implementation.

## Screenshots

![Dashboard](docs/assets/dashboard.png)

![Risk assessment](docs/assets/risk-assessment.png)

![Evidence center](docs/assets/evidence-center.png)

![Demo flow](docs/assets/demo-flow.gif)

See [Demo Guide](docs/DEMO.md) for the recommended walkthrough.
See [Production Mode](docs/PRODUCTION.md) for enabling real LLM refinement, LangSmith metadata, PostgreSQL, and Qdrant.
See [Test With Your OpenAI API Key](docs/TEST_WITH_OPENAI_KEY.md) for a local live-LLM smoke test and app runbook.
See [Production-Like Local Testing](docs/PRODUCTION_LIKE_TESTING.md) for a Docker stack with API-key auth, PostgreSQL, Qdrant, React, MCP, live LLM calls, and optional managed embeddings.

## Stack

- Python, FastAPI, Pydantic, SQLAlchemy
- LangGraph-compatible workflow abstraction with optional LangGraph integration
- RAG over a source-linked local Markdown compliance knowledge base with hybrid retrieval, metadata boosts, explainable reranking, citation quality, and evidence grading
- MCP/FastMCP server exposing tools, resources, and prompts
- PostgreSQL and Qdrant via Docker Compose, SQLite for fast local development and tests
- Optional OpenAI advisory mode and LangSmith trace metadata
- React product UI
- pytest evaluation and guardrail tests

## Features

- AI system inventory and structured intake
- Adaptive missing-information questions
- Risk classification with uncertainty and human-review flags
- Internal regulatory/policy retrieval with citations
- Legal-source manifest for article-level official corpus ingestion
- Requirement-to-control mapping
- Compliance gap analysis
- Remediation plan generation from gaps and missing evidence
- Evidence checklist generation with owner, due-date, expiry, source, checksum, retention, approval, and readiness lifecycle tracking
- Risk register and policy exception workflows with compensating controls, expiry queues, and audit events
- AI incident reporting, regulatory report queue, triage, resolution tracking, and audit events
- Structured audit trail for evidence updates and human review decisions
- Runtime readiness checks, production preflight release gate, and Docker healthchecks for production operations
- Runtime HTTP metrics in JSON and Prometheus text formats
- Configurable API hardening with security headers, request body limits, CORS allowlists, and tenant-aware rate limiting
- Request correlation IDs and consistent problem-style API error responses
- Bounded list endpoints with `limit` / `offset` pagination headers for production data volumes
- Named database migration registry with migration readiness checks
- AI system card and audit report generation
- Human review workflow: draft, approved, rejected, needs more evidence
- Review queue escalation signals and notification outbox for SLA breaches, high-risk gaps, and missing evidence
- Guardrails that prevent final compliance claims without human approval
- Evaluation tests for risk consistency, RAG relevance, structured outputs, and prompt-injection resistance
- Markdown and PDF exports for system cards and audit reports
- JSON and ZIP assessment and tenant-level audit packages for regulator, backup, or internal audit handoff
- Demo scenario pack for portfolio walkthroughs

## Evaluation Metrics

The MVP includes a reproducible evaluation suite exposed at `GET /evaluation/results`:

- risk classification consistency
- human approval bypass resistance
- retrieval grounding and source availability
- retrieval quality top-k recall over curated RAG cases
- AI system card section coverage
- evidence checklist completeness
- legal-advice guardrail behavior

LangSmith-compatible experiment payloads are exposed at `GET /evaluation/langsmith-experiment`; `POST /evaluation/langsmith-experiment/upload` uploads when `LANGSMITH_API_KEY` is configured.

## Demo Flow

1. Create an AI system using the UI or `POST /systems`.
2. Run `POST /systems/{system_id}/assess`.
3. Review risk level, retrieved requirements, mapped controls, gaps, evidence, system card, and audit report.
4. Submit a human review decision.
5. Search the requirements knowledge base and update evidence owners, due dates, expiry, approvals, and readiness.
6. Export the system card, audit report, or full audit package as Markdown/PDF/JSON/ZIP.

Example input:

```text
We use an AI assistant in HR to analyze CVs, rank candidates and generate recommendations for recruiters. The system processes personal data, stores embeddings of CVs and produces candidate fit scores. Final hiring decisions are reviewed by humans.
```

Expected outcome:

- High-risk candidate due to employment decision support and personal data processing
- Human review required
- Missing controls for oversight, bias testing, audit logging, retention, transparency, and evaluation
- Draft AI system card and audit report pending human review

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make ci
make migrate-db
uvicorn app.api.main:app --reload
```

In another terminal:

```bash
cd frontend/react_app
npm install
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

Docker:

```bash
docker compose up --build
```

Production-like Docker with live LLMs, Qdrant, PostgreSQL, React, and MCP:

```bash
# Fill OPENAI_API_KEY in .env.
make prod-up
make prod-ingest-qdrant
make prod-smoke
```

`make prod-up` starts FastAPI, React/Vite, MCP, PostgreSQL, and Qdrant from Docker Compose. The React and Python services are built from separate Dockerfile targets.

## Environment

Copy `.env.example` to `.env` and adjust values.

- `DATABASE_URL`: defaults to local SQLite if not provided
- `AI_GENERATION_MODE`: `deterministic` by default, or `openai`
- `LLM_PROVIDER`: `openai`, `openai_compatible`, or `anthropic` when LLM mode is enabled
- `OPENAI_API_KEY`: optional for OpenAI advisory mode
- `OPENAI_BASE_URL`: defaults to `https://api.openai.com/v1`
- `OPENAI_TIMEOUT_SECONDS`: request timeout for LLM calls
- `OPENAI_MAX_RETRIES`: retry count for transient LLM request failures
- `OPENAI_MAX_TOKENS`: maximum completion tokens for LLM refinement calls
- `LLM_PROMPT_COST_PER_1K_TOKENS`: optional prompt-token cost used for usage estimates
- `LLM_COMPLETION_COST_PER_1K_TOKENS`: optional completion-token cost used for usage estimates
- `ANTHROPIC_API_KEY`: optional for Anthropic LLM refinement
- `ANTHROPIC_MODEL`: defaults to `claude-3-5-sonnet-latest`
- `LANGSMITH_TRACING`: optional trace metadata
- `LANGSMITH_API_KEY`: optional for hosted LangSmith usage
- `VECTOR_DB`: `local` by default, or `qdrant` / `pinecone`
- `QDRANT_URL`: defaults to `http://localhost:6333`
- `QDRANT_COLLECTION`: defaults to `ai_governance_requirements`
- `PINECONE_API_KEY`: optional for Pinecone vector search
- `PINECONE_INDEX_HOST`: Pinecone index host URL for query/upsert requests
- `PINECONE_NAMESPACE`: Pinecone namespace for compliance requirements
- `EMBEDDING_PROVIDER`: `local_hash` by default, or `openai`
- `OPENAI_EMBEDDING_MODEL`: defaults to `text-embedding-3-small`
- `EMBEDDING_DIMENSIONS`: local deterministic embedding size for offline dev/test retrieval
- `AUTH_MODE`: `disabled` for local demos, or `api_key` for API-key protected deployments
- `PLATFORM_API_KEY`: shared API key used when `AUTH_MODE=api_key`
- `PLATFORM_API_KEY_SHA256`: optional SHA-256 hash of the shared API key; preferred over plaintext secret env vars where supported
- `DEFAULT_USER_ROLE`: fallback role, one of `viewer`, `auditor`, `compliance_reviewer`, `admin`
- `DEFAULT_TENANT_ID`: fallback workspace/tenant id for local or single-tenant deployments
- `CORS_ALLOWED_ORIGINS`: comma-separated browser origins allowed to call the API
- `SECURITY_HEADERS_ENABLED`: enables defensive HTTP headers, on by default
- `SECURITY_HSTS_ENABLED`: enables HSTS when the API is served only over HTTPS
- `MAX_REQUEST_BODY_BYTES`: rejects oversized API requests before route handling
- `API_RATE_LIMIT_PER_MINUTE`: optional in-memory per-tenant/caller limit; `0` disables it
- `REVIEW_SLA_HOURS`: default human-review SLA used by review queues and escalation notifications
- `REVIEW_MISSING_EVIDENCE_ESCALATION_THRESHOLD`: missing evidence count that triggers review attention
- `REVIEW_HIGH_RISK_CRITICAL_GAP_ESCALATION`: whether high-risk critical gaps trigger urgent escalation
- `NOTIFICATION_DELIVERY_MODE`: `manual` by default, or `webhook` to dispatch queued notifications
- `NOTIFICATION_WEBHOOK_URL`: fallback HTTPS webhook target for queued notification dispatch
- `NOTIFICATION_WEBHOOK_TIMEOUT_SECONDS`: outbound webhook timeout
- `MCP_TRANSPORT`: `stdio` locally, or an HTTP transport such as `streamable-http` for deployment
- `MCP_HOST` / `MCP_PORT`: MCP runtime bind settings

LLM prompt templates are versioned in `app/prompts/registry.py`; LLM tool calls include prompt version, model, latency, token metadata, schema-validation status, applied sections, and SHA-256 prompt/output fingerprints where available.

When Qdrant or Pinecone is configured, populate the persistent collection with:

```bash
make ingest-qdrant
make ingest-pinecone
```

## Agents

- AI System Intake Agent
- Missing Information Checker
- Risk Classification Agent
- Regulatory RAG Agent
- Control Mapping Agent
- Gap Analysis Agent
- Evidence Checklist Generator
- AI System Card Generator
- Audit Report Generator
- Human Review Node

## MCP Surface

Run the MCP server locally with:

```bash
make mcp
```

Tools:

- `classify_ai_system_risk`
- `search_regulatory_requirements`
- `map_requirement_to_control`
- `generate_evidence_checklist`
- `generate_ai_system_card`
- `generate_audit_report`
- `create_compliance_task`
- `calculate_compliance_score`

Resources:

- `compliance://policies/internal-ai-policy`
- `compliance://policies/data-retention-policy`
- `compliance://policies/human-oversight-policy`
- `compliance://policies/model-evaluation-policy`
- `compliance://regulations/eu-ai-act-summary`
- `compliance://regulations/gdpr-summary`
- `compliance://regulations/dora-summary`
- `compliance://regulations/nis2-summary`
- `compliance://controls/human-oversight`
- `compliance://controls/audit-logging`
- `compliance://controls/evaluation`
- `compliance://controls/security-testing`

Prompts:

- `risk_classification_prompt`
- `regulatory_retrieval_prompt`
- `gap_analysis_prompt`
- `control_mapping_prompt`
- `system_card_prompt`
- `audit_report_prompt`
- `human_review_prompt`

## Limitations

- Regulatory documents are source-linked article-level governance records for product testing, not a complete legal corpus or legal advice.
- The MVP uses deterministic policy logic by default for reproducible tests.
- Risk results are preliminary and require human compliance/legal review.
- Retrieval uses local hybrid lexical + metadata ranking with query expansion, explainable reranking, matched-term evidence, citation-quality labels, and evidence grading by default. Qdrant and Pinecone adapters are available as persistent vector-store extension points.
- Rich RAG search is exposed through `GET /requirements/search?q=...` with optional `jurisdiction`, `document_type`, `category`, `tags`, and `authority` filters.
- Legal source readiness is exposed through `GET /requirements/legal-sources`; it shows file availability, expected article coverage, parsed locators, missing required locators, content hashes, blockers, warnings, and next actions.
- `make validate-legal-sources` validates manifest completeness and exits non-zero until official full-text sources are locally available, marked `available`, and sufficiently covered.
- `scripts/register_legal_source.py` registers a local official-source Markdown file in `data/legal_sources_manifest.json`, including optional expected article counts and required locators.

## Portfolio Value

- Built an AI Governance & Compliance Intelligence Platform using LangGraph-style orchestration, RAG, MCP, FastAPI, PostgreSQL, and React to classify AI system risk, map requirements to controls, identify gaps, and generate audit-ready AI system cards.
- Designed agentic workflows for intake, adaptive follow-up questioning, risk classification, regulatory retrieval, control mapping, evidence generation, audit reporting, and human compliance review.
- Implemented a RAG-based compliance knowledge base over regulatory summaries and internal AI policies to ground recommendations.
- Created guardrails ensuring AI-generated compliance assessments remain draft-only until approved by a reviewer.
- Developed automated tests for structured output validity, groundedness, prompt-injection resistance, policy mapping quality, and approval workflow reliability.
