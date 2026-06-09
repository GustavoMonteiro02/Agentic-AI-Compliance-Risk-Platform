from pathlib import Path

from app.rag.ingest import ingest_summary


def test_rag_ingest_summarizes_markdown_knowledge_base():
    summary = ingest_summary(Path("data"))

    assert summary["chunk_count"] >= 10
    assert "policies/internal_ai_policy.md" in summary["sources"]
