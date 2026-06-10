# Production Mode

The platform runs locally without credentials in deterministic mode, but it is designed to run with real LLM-backed refinement in production.

## Required Services

- FastAPI backend
- PostgreSQL database
- Streamlit frontend
- Optional Qdrant vector database
- Optional OpenAI-compatible LLM provider
- Optional LangSmith observability

## Environment

```bash
DATABASE_URL=postgresql+psycopg2://postgres:postgres@postgres:5432/ai_governance
AI_GENERATION_MODE=openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=ai-governance-compliance-platform
VECTOR_DB=qdrant
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=ai_governance_requirements
EMBEDDING_DIMENSIONS=128
AUTH_MODE=api_key
PLATFORM_API_KEY=change-me
DEFAULT_USER_ROLE=viewer
```

## LLM Behavior

The deterministic workflow always runs first. When `AI_GENERATION_MODE=openai` and `OPENAI_API_KEY` are set, the LangGraph workflow runs an additional `llm_refiner` node that refines:

- risk classification rationale
- mapped controls
- gap analysis
- evidence checklist
- AI system card Markdown
- audit report Markdown

The LLM output is validated with Pydantic before it can replace deterministic outputs. Failed LLM calls are logged in the graph state and do not break the assessment workflow.

Prompt templates are versioned in `app/prompts/registry.py`. Each LLM refinement tool call records the prompt name, prompt version, provider, model, latency, and token usage when the provider returns usage metadata. This keeps generated assessments auditable and makes prompt changes reviewable like code changes.

## Human Review Guardrail

Even in LLM mode, assessments remain `needs_review` until a reviewer explicitly approves, rejects, or requests more evidence. The LLM is not allowed to produce final legal-compliance claims.

## Access Control

Local development can run with `AUTH_MODE=disabled`. Production should set `AUTH_MODE=api_key` and provide `PLATFORM_API_KEY`. Clients send either `X-API-Key` or `Authorization: Bearer <key>`, plus optional `X-User` and `X-User-Role` headers.

Roles are hierarchical:

- `viewer`: read systems, assessments, requirements, reports, and evidence.
- `auditor`: viewer permissions plus evaluation results.
- `compliance_reviewer`: auditor permissions plus assessments, evidence updates, demo assessments, and review decisions.
- `admin`: full access, including system creation and updates.

## Runtime Check

Use:

```bash
curl http://127.0.0.1:8000/runtime/status
```

This reports whether LLM mode, LangSmith metadata, and vector DB settings are active.
It also reports active prompt versions so operators can tie generated outputs to the prompt registry.

## RAG Ingestion

The local fallback uses hybrid lexical, phrase, metadata, and citation-aware reranking. When Qdrant is available, ingest the same knowledge-base chunks into a persistent vector collection:

```bash
make ingest-qdrant
```

The Qdrant payload stores requirement metadata, tags, source URLs, effective dates, and citation labels. The default embedding provider is deterministic and local for repeatable development; production can replace it with managed embeddings behind the same vector-store contract.

## Run

```bash
docker compose up --build
```

Then open:

- API: `http://127.0.0.1:8000`
- UI: `http://127.0.0.1:8501`
