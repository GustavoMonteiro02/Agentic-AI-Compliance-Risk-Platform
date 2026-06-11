from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_requirements_are_seeded_from_knowledge_base():
    response = client.get("/requirements")

    assert response.status_code == 200
    requirements = response.json()
    assert len(requirements) >= 10
    assert any(item["requirement_code"].startswith("HUMAN_OVERSIGHT") for item in requirements)
    assert not any(item["requirement_code"].endswith("_MD") for item in requirements)


def test_requirements_search_filters_seeded_requirements():
    response = client.get("/requirements", params={"q": "prompt injection"})

    assert response.status_code == 200
    results = response.json()
    assert results
    assert any("PROMPT" in item["requirement_code"] or "prompt" in item["description"].lower() for item in results)


def test_requirements_rag_search_exposes_metadata_filters_and_scores():
    response = client.get(
        "/requirements/search",
        params={"q": "AI Act human oversight intervention", "jurisdiction": "EU", "document_type": "regulation"},
    )

    assert response.status_code == 200
    results = response.json()
    assert results
    assert all(item["jurisdiction"] == "EU" for item in results)
    assert all(item["document_type"] == "regulation" for item in results)
    assert any(item["locator"] == "Article 14" for item in results)
    assert {"lexical", "phrase", "metadata", "source_quality", "vector", "final"} <= set(
        results[0]["score_breakdown"]
    )
