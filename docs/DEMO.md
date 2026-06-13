# Demo Guide

This guide describes the portfolio demo path for the AI Governance & Compliance Intelligence Platform.

## Visual Flow

![Demo flow](assets/demo-flow.gif)

## Screenshots

### Dashboard

![Dashboard](assets/dashboard.png)

### Risk Assessment

![Risk assessment](assets/risk-assessment.png)

### Evidence Center

![Evidence center](assets/evidence-center.png)

## Recommended Demo Script

1. Open the React UI at `http://127.0.0.1:5173`.
2. Start at **1. Intake** and create an AI system from the recruitment screening scenario.
3. Open **2. Assessment map** and explain the LangGraph workflow output: risk, requirements, controls, evidence links, gaps, and review impact.
4. Open **Legal library** and search for `human oversight`.
5. Open **3. Evidence** and update one evidence item from `missing` to `uploaded`.
6. Download the system card, audit report, or ZIP audit package from **2. Assessment map**; Markdown or PDF exports remain available through the report endpoints.
7. Open **5. Human review** and request more evidence or approve with reviewer notes.
8. Open **Settings** and **History** to show runtime configuration, LLM usage, audit events, guardrails, and traceability.

## Optional Integrations

- Set `AI_GENERATION_MODE=openai` and `OPENAI_API_KEY` to enable optional OpenAI advisory text in the risk classifier.
- Set `LANGSMITH_TRACING=true` to include LangSmith trace metadata in tool-call logs.
- Run `docker compose up --build` to start PostgreSQL and Qdrant alongside the API.
- Set `VECTOR_DB=qdrant` to health-check the Qdrant-ready retrieval path while retaining local hybrid retrieval and reranking as the offline fallback.

The default local mode remains deterministic and credential-free.
