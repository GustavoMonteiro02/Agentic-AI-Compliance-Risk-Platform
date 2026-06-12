from app.rag.chunker import DocumentChunk
from app.rag.embeddings import LocalHashEmbeddingProvider, OpenAIEmbeddingProvider, build_embedding_provider
from app.rag.vector_store import LocalVectorStore, PineconeVectorStore, QdrantVectorStore


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
    assert payload["embedding_provider"] == "local_hash"


def test_pinecone_payload_contains_metadata_namespace_and_citation():
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
        tags=("privacy",),
    )
    payload = PineconeVectorStore("key", "https://index.example.test", "compliance")._payload(chunk)

    assert payload["metadata"]["jurisdiction"] == "EU"
    assert payload["citation"]["source_url"] == "https://example.test/source"
    assert payload["vector_db"] == "pinecone"
    assert payload["namespace"] == "compliance"


def test_openai_embedding_provider_parses_embedding_response(monkeypatch):
    class FakeResponse:
        status_code = 200
        headers = {}

        def raise_for_status(self):
            return None

        def json(self):
            return {"data": [{"embedding": [0.1, 0.2, 0.3]}]}

    monkeypatch.setattr("app.rag.embeddings.requests.post", lambda *args, **kwargs: FakeResponse())

    provider = OpenAIEmbeddingProvider(api_key="test", dimensions=3)

    assert provider.embed("human oversight") == [0.1, 0.2, 0.3]
    assert provider.provider_name == "openai"


def test_openai_embedding_provider_batches_inputs(monkeypatch):
    captured_payloads = []

    class FakeResponse:
        status_code = 200
        headers = {}

        def raise_for_status(self):
            return None

        def json(self):
            return {"data": [{"embedding": [0.1, 0.2]}, {"embedding": [0.3, 0.4]}]}

    def fake_post(*args, **kwargs):
        captured_payloads.append(kwargs["json"])
        return FakeResponse()

    monkeypatch.setattr("app.rag.embeddings.requests.post", fake_post)

    provider = OpenAIEmbeddingProvider(api_key="test", dimensions=2)

    assert provider.embed_many(["human oversight", "audit logging"]) == [[0.1, 0.2], [0.3, 0.4]]
    assert captured_payloads == [{"model": "text-embedding-3-small", "input": ["human oversight", "audit logging"]}]


def test_openai_embedding_provider_retries_rate_limits(monkeypatch):
    calls = []

    class RateLimitResponse:
        status_code = 429
        headers = {"retry-after": "0"}

        def raise_for_status(self):
            raise AssertionError("retryable response should not raise before final attempt")

    class SuccessResponse:
        status_code = 200
        headers = {}

        def raise_for_status(self):
            return None

        def json(self):
            return {"data": [{"embedding": [0.1, 0.2, 0.3]}]}

    def fake_post(*args, **kwargs):
        calls.append(kwargs)
        return RateLimitResponse() if len(calls) == 1 else SuccessResponse()

    monkeypatch.setattr("app.rag.embeddings.requests.post", fake_post)
    monkeypatch.setattr("app.rag.embeddings.time.sleep", lambda seconds: None)

    provider = OpenAIEmbeddingProvider(api_key="test", dimensions=3, max_retries=1)

    assert provider.embed("human oversight") == [0.1, 0.2, 0.3]
    assert len(calls) == 2


def test_embedding_factory_requires_openai_key():
    class Settings:
        embedding_provider = "openai"
        openai_api_key = None
        openai_embedding_model = "text-embedding-3-small"
        embedding_dimensions = 1536

    try:
        build_embedding_provider(Settings())
    except ValueError as exc:
        assert "OPENAI_API_KEY" in str(exc)
    else:
        raise AssertionError("Expected missing OpenAI API key to fail")
