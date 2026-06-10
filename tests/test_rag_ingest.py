from pathlib import Path

from app.rag.ingest import ingest_summary
from app.rag.chunker import parse_markdown_requirements


def test_rag_ingest_summarizes_markdown_knowledge_base():
    summary = ingest_summary(Path("data"))

    assert summary["chunk_count"] >= 10
    assert "policies/internal_ai_policy.md" in summary["sources"]
    assert summary["legal_sources"]["manifest"] == "2026-06-10"


def test_rag_ingest_ignores_document_title_headers():
    summary = ingest_summary(Path("data"))

    assert summary["chunk_count"] < 40


def test_article_level_legal_source_chunks_include_locator_and_hash():
    text = Path("data/legal_sources/eu_ai_act_articles.md").read_text(encoding="utf-8")
    chunks = parse_markdown_requirements("legal_sources/eu_ai_act_articles.md", text)

    article_14 = next(chunk for chunk in chunks if chunk.locator == "Article 14")
    assert "human oversight" in article_14.category
    assert article_14.source_url == "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"
    assert article_14.content_hash
