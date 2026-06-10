from app.rag.chunker import DocumentChunk
from app.rag.embeddings import LocalHashEmbeddingProvider
from app.rag.vector_store import LocalVectorStore, QdrantVectorStore


def test_local_hash_embeddings_are_deterministic_and_normalized():
    provider = LocalHashEmbeddingProvider(dimensions=16)

    first = provider.embed("human oversight human review")
    second = provider.embed("human oversight human review")

    assert first == second
    assert len(first) == 16
    assert any(value != 0 for value in first)
    assert max(abs(value) for value in first) <= 1


def test_local_vector_store_exposes_loaded_chunks():
    chunk = DocumentChunk("REQ_1", "Requirement", "source.md", "general", "Requirement text")
    store = LocalVectorStore()

    store.add([chunk])

    assert store.chunks() == [chunk]


def test_qdrant_payload_contains_metadata_and_citation():
    chunk = DocumentChunk(
        requirement_id="REQ_1",
        title="Requirement",
        source="regulations/example.md",
        category="data protection",
        text="Requirement text",
        jurisdiction="EU",
        document_type="regulation",
        authority="European Union",
        source_url="https://example.test/source",
        effective_date="2026-01-01",
        tags=("privacy", "retention"),
    )
    payload = QdrantVectorStore("http://localhost:6333", "test")._payload(chunk)

    assert payload["metadata"]["jurisdiction"] == "EU"
    assert payload["citation"]["source_url"] == "https://example.test/source"
    assert payload["tags"] == ["privacy", "retention"]
