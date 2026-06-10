from app.rag.retriever import LocalComplianceRetriever


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
