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

1. Open the Streamlit UI at `http://127.0.0.1:8501`.
2. Go to **Demo Scenarios** and run `Recruitment CV Screening Assistant`.
3. Open **Assessment** and explain the LangGraph workflow output: risk, requirements, controls, and gaps.
4. Open **Requirements** and search for `human oversight`.
5. Open **Evidence** and update one evidence item from `missing` to `uploaded`.
6. Open **System Card** and **Audit Report**, then download Markdown or PDF.
7. Open **Human Review** and request more evidence or approve with reviewer notes.
8. Open **Evaluation** to show guardrail and groundedness metrics.

## Optional Integrations

- Set `AI_GENERATION_MODE=openai` and `OPENAI_API_KEY` to enable optional OpenAI advisory text in the risk classifier.
- Set `LANGSMITH_TRACING=true` to include LangSmith trace metadata in tool-call logs.
- Run `docker compose up --build` to start PostgreSQL and Qdrant alongside the API.
- Set `VECTOR_DB=qdrant` to health-check the Qdrant-ready retrieval path while retaining local hybrid retrieval and reranking as the offline fallback.

The default local mode remains deterministic and credential-free.
