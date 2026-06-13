from pathlib import Path

from app.rag.ingest import ingest_pinecone, ingest_summary, legal_source_summary, validate_legal_sources
from app.rag.legal_sources import load_legal_sources_manifest, register_legal_source
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


def test_pinecone_ingest_requires_credentials(monkeypatch):
    class Settings:
        pinecone_api_key = None
        pinecone_index_host = None

    monkeypatch.setattr("app.rag.ingest.get_settings", lambda: Settings())

    try:
        ingest_pinecone(Path("data"))
    except ValueError as exc:
        assert "PINECONE_API_KEY" in str(exc)
    else:
        raise AssertionError("Expected Pinecone ingestion to require credentials")


def test_legal_source_summary_includes_validation_gate():
    summary = legal_source_summary(Path("data"))

    assert summary["validation"]["ready"] is False
    assert any("official_source_extract" in warning for warning in summary["validation"]["warnings"])
    assert any("8/113" in warning for warning in summary["validation"]["warnings"])
    assert summary["validation"]["errors"] == []
    ai_act = next(source for source in summary["sources"] if source["id"] == "eu-ai-act")
    assert ai_act["coverage_percent"] < 10
    assert set(ai_act["parsed_locators"]) == {"Article 9", "Article 10", "Article 11", "Article 12", "Article 13", "Article 14", "Article 15", "Article 16"}
    assert ai_act["missing_required_locators"] == []
    assert ai_act["readiness"]["ready"] is False
    assert "partial_article_coverage" in ai_act["readiness"]["warnings"]
    gdpr = next(source for source in summary["sources"] if source["id"] == "gdpr")
    assert gdpr["readiness"]["blockers"] == []
    assert set(gdpr["parsed_locators"]) == {"Article 5", "Article 6", "Article 9", "Article 22", "Article 30", "Article 32", "Article 35"}


def test_legal_source_validation_passes_complete_local_sources():
    validation = validate_legal_sources(
        [
            {
                "id": "source-1",
                "title": "Official source",
                "jurisdiction": "EU",
                "authority": "Authority",
                "source_url": "https://example.test/source",
                "document_type": "regulation",
                "local_path": "legal/source.md",
                "ingestion_status": "available",
                "available": True,
                "chunk_count": 3,
                "missing_required_locators": [],
            }
        ]
    )

    assert validation == {"ready": True, "errors": [], "warnings": []}


def test_register_legal_source_updates_manifest(tmp_path):
    legal_dir = tmp_path / "legal_sources"
    legal_dir.mkdir()
    source_file = legal_dir / "official.md"
    source_file.write_text(
        "# Official\n\n## ARTICLE_1 Scope\nLocator: Article 1\nOfficial source text.",
        encoding="utf-8",
    )
    (tmp_path / "legal_sources_manifest.json").write_text('{"version": "test", "sources": []}', encoding="utf-8")

    registered = register_legal_source(
        tmp_path,
        {
            "id": "official-test",
            "title": "Official Test Source",
            "jurisdiction": "EU",
            "authority": "European Union",
            "source_url": "https://example.test/official",
            "document_type": "regulation",
            "local_path": "legal_sources/official.md",
        },
    )
    manifest = load_legal_sources_manifest(tmp_path)

    assert registered["ingestion_status"] == "available"
    assert manifest["sources"][0]["id"] == "official-test"
    assert legal_source_summary(tmp_path)["validation"]["ready"] is True
