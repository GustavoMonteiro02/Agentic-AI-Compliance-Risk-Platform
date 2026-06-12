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
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=128
AUTH_MODE=api_key
PLATFORM_API_KEY=change-me
DEFAULT_USER_ROLE=viewer
DEFAULT_TENANT_ID=default
CORS_ALLOWED_ORIGINS=https://governance.example.com
SECURITY_HEADERS_ENABLED=true
SECURITY_HSTS_ENABLED=true
MAX_REQUEST_BODY_BYTES=1048576
API_RATE_LIMIT_PER_MINUTE=120
```

## LLM Behavior

The deterministic workflow always runs first. When `AI_GENERATION_MODE=openai` or `AI_GENERATION_MODE=llm` is set and the selected provider has credentials, the LangGraph workflow runs an additional `llm_refiner` node that refines:

- risk classification rationale
- mapped controls
- gap analysis
- evidence checklist
- AI system card Markdown
- audit report Markdown

The LLM output is validated with Pydantic before it can replace deterministic outputs. Failed LLM calls are logged in the graph state and do not break the assessment workflow. Production deployments can set `LLM_PROVIDER=openai`, `LLM_PROVIDER=openai_compatible`, or `LLM_PROVIDER=anthropic`, and tune `OPENAI_BASE_URL`, `OPENAI_TIMEOUT_SECONDS`, `OPENAI_MAX_RETRIES`, `OPENAI_MAX_TOKENS`, `ANTHROPIC_BASE_URL`, and `ANTHROPIC_MODEL` without code changes.

Prompt templates are versioned in `app/prompts/registry.py`. Each LLM refinement tool call records the prompt name, prompt version, provider, model, latency, retry attempts, and token usage when the provider returns usage metadata. This keeps generated assessments auditable and makes prompt changes reviewable like code changes.

## Evaluation Experiments

`GET /evaluation/langsmith-experiment` returns a LangSmith-compatible offline regression payload for the evaluation suite. `POST /evaluation/langsmith-experiment/upload` sends the runs to the configured LangSmith API when `LANGSMITH_API_KEY` is available; without credentials, the payload remains locally inspectable and CI-safe.

## Human Review Guardrail

Even in LLM mode, assessments remain `needs_review` until a reviewer explicitly approves, rejects, or requests more evidence. The LLM is not allowed to produce final legal-compliance claims.

## Access Control

Local development can run with `AUTH_MODE=disabled`. Production should set `AUTH_MODE=api_key` and provide `PLATFORM_API_KEY`. Clients send either `X-API-Key` or `Authorization: Bearer <key>`, plus optional `X-User`, `X-User-Role`, and `X-Tenant-ID` headers.
Browser deployments should set `CORS_ALLOWED_ORIGINS` to a comma-separated allowlist such as `https://governance.example.com`; CORS is closed by default when unset.

## API Hardening

Security headers are enabled by default with `SECURITY_HEADERS_ENABLED=true`, adding frame, MIME sniffing, referrer, permissions, cache, and cross-origin opener protections to API responses. Enable `SECURITY_HSTS_ENABLED=true` only when the public API is served exclusively through HTTPS.

`MAX_REQUEST_BODY_BYTES` rejects oversized request bodies before route handlers run. `API_RATE_LIMIT_PER_MINUTE` enables an in-memory tenant/caller rate limit using `X-Tenant-ID` plus API key, user, or client IP; keep it at `0` behind a dedicated gateway rate limiter, or set a positive value for standalone deployments.

Every response includes `X-Request-ID`. Clients may provide this header to correlate API calls with gateway logs, traces, and audit workflows. HTTP and validation errors use a problem-style JSON shape with `status`, `detail`, `instance`, `request_id`, and `error.code`; the legacy `detail` field is preserved for existing clients.

Roles are hierarchical:

- `viewer`: read systems, assessments, requirements, reports, and evidence.
- `auditor`: viewer permissions plus evaluation results.
- `compliance_reviewer`: auditor permissions plus assessments, evidence updates, demo assessments, and review decisions.
- `admin`: full access, including system creation and updates.

## Multi-Tenancy

Systems, assessments, evidence, reports, review queues, and audit events are scoped by tenant. The tenant comes from `X-Tenant-ID`, falling back to `DEFAULT_TENANT_ID`. This keeps workspaces isolated while preserving a simple local development mode.

## Audit Trail

Evidence updates and human review decisions write immutable-style audit events to `audit_events`. Auditors can retrieve them through:

```bash
curl -H "X-API-Key: $PLATFORM_API_KEY" -H "X-User-Role: auditor" \
  http://127.0.0.1:8000/audit/assessments/{assessment_id}/events
```

For regulator or internal audit handoff, auditors can export a complete assessment package:

```bash
curl -H "X-API-Key: $PLATFORM_API_KEY" -H "X-User-Role: auditor" \
  http://127.0.0.1:8000/audit/assessments/{assessment_id}/package

curl -H "X-API-Key: $PLATFORM_API_KEY" -H "X-User-Role: auditor" \
  -o audit_package.zip \
  http://127.0.0.1:8000/audit/assessments/{assessment_id}/package.zip
```

The package includes the tenant-scoped system record, assessment snapshot, mapped controls, gaps, evidence, risks, policy exceptions, incidents, human reviews, tool calls, audit events, system card, audit report, and a summary manifest.

Evidence records support operational audit metadata such as source system, file URL, checksum/hash, collection date, expiry date, retention date, reviewer notes, and custom metadata. These fields are included in evidence APIs and audit packages so exported evidence can be reconciled against external GRC, ticketing, storage, or data-governance systems.

## Notifications

Review escalations can be converted into queued notification events:

```bash
curl -X POST -H "X-API-Key: $PLATFORM_API_KEY" -H "X-User-Role: compliance_reviewer" \
  "http://127.0.0.1:8000/reviews/escalations/notifications?channel=email&recipient=compliance@example.com"

curl -H "X-API-Key: $PLATFORM_API_KEY" -H "X-User-Role: auditor" \
  "http://127.0.0.1:8000/notifications?event_type=review_escalation&status=queued"
```

The current delivery model is an internal outbox: events are deduplicated by assessment and escalation level, tenant-scoped, audit logged, and included in audit packages. External Slack, email, or ticketing delivery can consume queued events from this stable API surface.

## Runtime Check

Use:

```bash
curl http://127.0.0.1:8000/runtime/status
curl http://127.0.0.1:8000/runtime/readiness
curl http://127.0.0.1:8000/runtime/metrics
curl http://127.0.0.1:8000/runtime/metrics.prom
```

This reports whether LLM mode, LangSmith metadata, API hardening, and vector DB settings are active.
It also reports active prompt versions so operators can tie generated outputs to the prompt registry.
Readiness validates database connectivity, knowledge-base loading, auth configuration, API hardening, LLM configuration, and vector DB availability when Qdrant or Pinecone is enabled.
Metrics expose request counts, error counts, status counts, and average route latency. The `.prom` endpoint emits Prometheus-compatible text for lightweight scraping.

## Database Migrations

The application records named schema migrations in `schema_migrations` and applies missing migrations during startup after SQLAlchemy creates known tables. Operators can run the same path explicitly before a release:

```bash
make migrate-db
```

`/runtime/readiness` includes `database_migrations.current`, `applied`, and `pending` so deployments can fail fast when the database schema is not current.

## Pagination

List endpoints accept `limit` and `offset` query parameters with a maximum `limit` of `250`. Responses remain plain JSON arrays for compatibility and include `X-Total-Count`, `X-Limit`, and `X-Offset` headers so operational clients can page through larger tenants safely.

## MCP Runtime

The MCP surface can run as its own process:

```bash
make mcp
```

Local development defaults to `MCP_TRANSPORT=stdio`. Container deployments can set `MCP_TRANSPORT=streamable-http`, `MCP_HOST=0.0.0.0`, and `MCP_PORT=9000`; Docker Compose includes an `mcp` service using `scripts/run_mcp_server.py`.

## RAG Ingestion

The local fallback uses hybrid lexical, phrase, metadata, query-expansion, and citation-aware reranking. `GET /requirements/search` exposes the same retrieval path with metadata filters for jurisdiction, document type, category, tags, and authority. When Qdrant or Pinecone is available, ingest the same knowledge-base chunks into a persistent vector collection:

```bash
make ingest-qdrant
make ingest-pinecone
```

The Qdrant and Pinecone payloads store requirement metadata, tags, source URLs, effective dates, and citation labels. Pinecone deployments set `VECTOR_DB=pinecone`, `PINECONE_API_KEY`, `PINECONE_INDEX_HOST`, and optionally `PINECONE_NAMESPACE`. The default embedding provider is deterministic and local for repeatable development. Production can set `EMBEDDING_PROVIDER=openai` to use managed OpenAI embeddings behind the same vector-store contract.

For full legal corpora, add official article-level Markdown files under `data/legal_sources/` and register them in `data/legal_sources_manifest.json`. The manifest records source URL, jurisdiction, document type, ingestion status, and local path. Chunks include locator and content hash metadata for citation-grade retrieval.
Operators can inspect corpus readiness through `GET /requirements/legal-sources` and `/runtime/readiness`; both expose source counts, local availability, chunk counts, and whether every manifest source is locally available.
Use `make validate-legal-sources` as a release gate when promoting a full official corpus. The command exits non-zero while manifest sources are missing, only sample extracts are present, or article-level chunks cannot be parsed.
Use `scripts/register_legal_source.py` to register a new local official-source Markdown file with jurisdiction, authority, source URL, document type, and local path metadata before running vector ingestion.

## Release Gate

Before pushing a production branch, run:

```bash
make ci
```

The CI gate runs a repository security/configuration scan and the pytest suite. GitHub Actions runs the same checks on push and pull request.
Docker images include a liveness healthcheck, and Docker Compose includes service healthchecks for the API, PostgreSQL, and Qdrant.

## Run

```bash
docker compose up --build
```

Then open:

- API: `http://127.0.0.1:8000`
- UI: `http://127.0.0.1:8501`

The React SaaS UI is available in `frontend/react_app` and can be run with `npm run dev` after installing its dependencies. It uses the same API key, role, and tenant headers as the Streamlit UI through `VITE_*` environment variables.
GitHub Actions installs Node.js and runs `npm install && npm run build` for the React command center on push and pull request.
