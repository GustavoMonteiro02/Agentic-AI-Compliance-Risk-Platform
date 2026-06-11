# Technical Backlog

## v0.1 Core MVP - Done

- FastAPI service with health, systems, assessments, reviews, reports, and evaluation routes.
- SQLAlchemy persistence with SQLite dev support and PostgreSQL compatibility.
- Deterministic agent workflow covering intake, risk, RAG, controls, gaps, evidence, card, report, and human review.
- Streamlit UI for dashboard, intake, assessment, evidence, report, and review queue.
- pytest coverage for core guardrails and API.

## v0.2 RAG Knowledge Base - Mostly Done

- Add richer policy and regulatory summaries.
- Add Qdrant and Pinecone integrations behind the existing metadata-aware hybrid retriever interface.
- Add document ingestion CLI and chunk metadata.
- Retrieval quality evaluation dataset and top-k recall metric.

## v0.3 Evidence and Audit Reports - Mostly Done

- Markdown and PDF export.
- Evidence upload metadata and approval statuses.
- Remediation plan generation.

## v0.4 Human Review Workflow - Done

- Reviewer assignment and queues.
- Risk override with justification.
- Approval history and audit log.
- Stronger status transition rules.

## v0.5 MCP Server - Runtime Ready

- FastMCP runtime server.
- Configurable MCP runtime entrypoint, Make target, and Docker Compose service.
- Agent calls via MCP client.
- Full resource and prompt catalog.

## v0.6 Evaluation and Guardrails - Done

- RAG groundedness scoring.
- Prompt-injection challenge set.
- Structured output regression tests.
- LangSmith experiment integration.

## v1.0 Portfolio Ready

- Screenshots and demo GIF.
- Architecture diagrams.
- Deployment guide.
- CV and interview talking points.
- Multi-provider LLM refinement configuration for OpenAI, OpenAI-compatible endpoints, and Anthropic.
