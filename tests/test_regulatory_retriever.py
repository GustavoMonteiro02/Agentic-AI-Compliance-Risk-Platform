from app.rag.retriever import LocalComplianceRetriever, RetrievalFilters


def test_rag_retrieves_relevant_human_oversight_policy():
    results = LocalComplianceRetriever().search("employment personal data human oversight audit logging")
    ids = {item["requirement_id"] for item in results}

    assert any("HUMAN_OVERSIGHT" in requirement_id for requirement_id in ids)
    assert all(item["source"] for item in results)
    assert all(item["metadata"]["document_type"] for item in results)


def test_retriever_marks_local_hybrid_rerank_mode_by_default():
    results = LocalComplianceRetriever().search("human oversight")

    assert results
    assert results[0]["retriever"] == "local-hybrid-rerank"
    assert results[0]["score"] > 0
    assert {"lexical", "phrase", "metadata", "source_quality", "vector", "final"} <= set(results[0]["score_breakdown"])
    assert results[0]["citation"]["requirement_id"] == results[0]["requirement_id"]


def test_retriever_surfaces_source_metadata_for_regulations():
    results = LocalComplianceRetriever().search("gdpr personal data lawful basis retention")

    top = results[0]
    assert "DATA_PROTECTION_GDPR" in top["requirement_id"]
    assert top["jurisdiction"] == "EU"
    assert top["document_type"] == "regulation"
    assert top["source_url"] == "https://eur-lex.europa.eu/eli/reg/2016/679/oj"


def test_retriever_can_return_article_level_locator():
    results = LocalComplianceRetriever().search("AI Act Article 14 human oversight intervention")

    assert any(item.get("locator") == "Article 14" for item in results)


def test_retriever_expands_domain_terms_for_hybrid_search():
    results = LocalComplianceRetriever().search("cv screening")

    assert results
    assert any("HUMAN_OVERSIGHT" in item["requirement_id"] for item in results)
    assert any("personal data" in item["summary"].lower() or "gdpr" in item["summary"].lower() for item in results)


def test_retriever_filters_by_metadata_before_reranking():
    filters = RetrievalFilters.from_values(jurisdiction="EU", document_type="regulation")
    results = LocalComplianceRetriever().search("human oversight intervention", filters=filters)

    assert results
    assert all(item["jurisdiction"] == "EU" for item in results)
    assert all(item["document_type"] == "regulation" for item in results)


def test_retriever_can_use_pinecone_vector_scores(monkeypatch):
    class Settings:
        from pathlib import Path

        knowledge_base_path = Path("data")
        vector_db = "pinecone"
        pinecone_api_key = "test-key"
        pinecone_index_host = "https://index.example.test"
        pinecone_namespace = "compliance"
        embedding_provider = "local_hash"
        embedding_dimensions = 128

    monkeypatch.setattr("app.rag.retriever.get_settings", lambda: Settings())
    monkeypatch.setattr("app.rag.vector_store.PineconeVectorStore.health", lambda self: {"available": True})
    monkeypatch.setattr(
        "app.rag.vector_store.PineconeVectorStore.search",
        lambda self, query, limit=12: [
            {"metadata": {"requirement_id": "EU_AI_ACT_ARTICLE_14_HUMAN_OVERSIGHT"}, "score": 0.99}
        ],
    )

    results = LocalComplianceRetriever().search("Article 14", top_k=3)

    assert results[0]["requirement_id"] == "EU_AI_ACT_ARTICLE_14_HUMAN_OVERSIGHT"
    assert results[0]["retriever"] == "local-hybrid-rerank-pinecone-ready"
