# Test With Your OpenAI API Key

Use this path when you want to test live LLM refinement locally.

## 1. Create `.env`

```bash
cp .env.example .env
```

Edit `.env` and set:

```bash
AI_GENERATION_MODE=llm
OPENAI_API_KEY=your-openai-api-key
```

Keep `AUTH_MODE=disabled` for local UI testing. Use `AUTH_MODE=api_key` only when you also want to test platform API authentication.

## 2. Run database migrations

```bash
make migrate-db
```

## 3. Smoke test the LLM

```bash
make llm-smoke
```

Expected result:

- `LLM smoke test passed.`
- provider/model metadata
- token and latency metadata when the provider returns it

## 4. Start the API

```bash
make api
```

Then verify:

```bash
curl http://127.0.0.1:8000/runtime/status
curl http://127.0.0.1:8000/runtime/preflight?target=development
```

`/runtime/status` should show `llm_enabled: true`.

## 5. Start the React UI

In another terminal:

```bash
make ui
```

Open:

```text
http://127.0.0.1:5173
```

Create or run an assessment. The workflow will run deterministic controls first, then the `llm_refiner` node if your key is valid.
The assessment form only shows live LLM providers that are configured in `.env`, and lets you choose provider, model, token limit, timeout, retries, and temperature for that run.

## 6. Check LLM usage

```bash
curl http://127.0.0.1:8000/assessments/llm-usage
```

This returns LLM call counts, tokens, latency, provider/model, prompt versions, and estimated cost if cost env vars are set.
