from app.rag.retriever import LocalComplianceRetriever


def test_rag_retrieves_relevant_human_oversight_policy():
    results = LocalComplianceRetriever().search("employment personal data human oversight audit logging")
    ids = {item["requirement_id"] for item in results}

    assert any("HUMAN_OVERSIGHT" in requirement_id for requirement_id in ids)
    assert all(item["source"] for item in results)

