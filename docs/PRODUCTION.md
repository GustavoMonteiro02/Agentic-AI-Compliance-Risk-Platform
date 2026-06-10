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

## Human Review Guardrail

Even in LLM mode, assessments remain `needs_review` until a reviewer explicitly approves, rejects, or requests more evidence. The LLM is not allowed to produce final legal-compliance claims.

## Runtime Check

Use:

```bash
curl http://127.0.0.1:8000/runtime/status
```

This reports whether LLM mode, LangSmith metadata, and vector DB settings are active.

## Run

```bash
docker compose up --build
```

Then open:

- API: `http://127.0.0.1:8000`
- UI: `http://127.0.0.1:8501`

