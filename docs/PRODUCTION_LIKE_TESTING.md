# Production-Like Local Testing

This path runs the app as close to production as practical on a laptop: FastAPI, PostgreSQL, Qdrant, Streamlit, React, MCP, API-key auth, live OpenAI LLM calls, and OpenAI embeddings for vector search.

## Required Keys

Only one external provider key is required for the default production-like stack:

```bash
OPENAI_API_KEY=replace-with-your-openai-api-key
```

You also need to create one local platform API key. This is not from an external service; choose a strong random value and use the same value for backend clients and the React UI:

```bash
PLATFORM_API_KEY=change-me
VITE_PLATFORM_API_KEY=change-me
```

Optional keys:

- `LANGSMITH_API_KEY`: hosted trace/evaluation upload.
- `ANTHROPIC_API_KEY`: only needed when `LLM_PROVIDER=anthropic`.
- `PINECONE_API_KEY` and `PINECONE_INDEX_HOST`: only needed when `VECTOR_DB=pinecone`.
- `NOTIFICATION_WEBHOOK_URL`: only needed when `NOTIFICATION_DELIVERY_MODE=webhook`.

The assessment UI discovers configured LLM providers from `GET /runtime/llm-options`. It shows only providers with keys configured in `.env`, then lets you choose mode, provider, model, token limit, timeout, retry count, and temperature per assessment.

## Configure

Edit `.env` and set:

```bash
OPENAI_API_KEY=...
```

The local `PLATFORM_API_KEY` and `VITE_PLATFORM_API_KEY` are already generated in `.env`. They must stay equal.

For OpenAI + LangSmith + the full local feature set, use:

```bash
AI_GENERATION_MODE=llm
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4.1-mini
VECTOR_DB=qdrant
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=ai-governance-compliance-platform
AUTH_MODE=api_key
PLATFORM_API_KEY=change-me
VITE_PLATFORM_API_KEY=change-me
MCP_TRANSPORT=streamable-http
NOTIFICATION_DELIVERY_MODE=manual
```

Optional integrations remain disabled until their keys are set:

- Add `ANTHROPIC_API_KEY` to make Anthropic appear in the UI provider selector.
- Add `PINECONE_API_KEY` and `PINECONE_INDEX_HOST`, then set `VECTOR_DB=pinecone`, to test Pinecone instead of local Qdrant.
- Set `NOTIFICATION_DELIVERY_MODE=webhook` and `NOTIFICATION_WEBHOOK_URL=https://...` to test real outbound notification dispatch.

Keep these defaults for a full live local test:

```bash
AI_GENERATION_MODE=llm
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=openai
VECTOR_DB=qdrant
AUTH_MODE=api_key
```

`.env` is ignored by git. Do not commit real keys.

## Start The Stack

```bash
make prod-up
```

Open:

- API docs: http://127.0.0.1:8000/docs
- Streamlit UI: http://127.0.0.1:8501
- React command center: http://127.0.0.1:5173
- MCP HTTP server: http://127.0.0.1:9000
- Qdrant: http://127.0.0.1:6333/dashboard

## Ingest RAG Vectors

In another terminal:

```bash
make prod-ingest-qdrant
```

With `EMBEDDING_PROVIDER=openai`, this creates OpenAI embeddings for the local regulatory and policy knowledge base and stores them in Qdrant.

## Run The Production Smoke Test

```bash
make prod-smoke
```

The smoke test waits for the API, checks runtime status, checks production preflight, creates a production-like HR AI system, runs an assessment, verifies LLM usage was recorded, and searches the RAG corpus through the API.

Expected local caveats:

- `release_ready` may be false while testing on local HTTP because HSTS is disabled.
- Legal-source warnings may remain until you add complete official article-level legal corpora under `data/legal_sources/`.
- The smoke test should still record non-zero LLM calls when `AI_GENERATION_MODE=llm` and `OPENAI_API_KEY` is valid.

## Manual API Checks

```bash
set -a
. ./.env
set +a

curl -H "X-API-Key: $PLATFORM_API_KEY" -H "X-User-Role: admin" \
  http://127.0.0.1:8000/runtime/status

curl -H "X-API-Key: $PLATFORM_API_KEY" -H "X-User-Role: admin" \
  http://127.0.0.1:8000/runtime/readiness

curl -H "X-API-Key: $PLATFORM_API_KEY" -H "X-User-Role: admin" \
  "http://127.0.0.1:8000/runtime/preflight?target=production"
```

## Stop

```bash
make prod-down
```
