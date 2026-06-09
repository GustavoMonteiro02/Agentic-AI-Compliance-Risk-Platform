from app.rag.chunker import DocumentChunk


class LocalVectorStore:
    """Small in-memory store used by the MVP before Qdrant/Pinecone integration."""

    def __init__(self) -> None:
        self._chunks: list[DocumentChunk] = []

    def add(self, chunks: list[DocumentChunk]) -> None:
        self._chunks.extend(chunks)

    def count(self) -> int:
        return len(self._chunks)

    def sources(self) -> list[str]:
        return sorted({chunk.source for chunk in self._chunks})


class QdrantVectorStore:
    """Qdrant-ready adapter used when VECTOR_DB=qdrant.

    The MVP keeps lexical retrieval as a fallback, but this gives the project a
    concrete extension point and health check for a Dockerized Qdrant service.
    """

    def __init__(self, url: str, collection: str) -> None:
        self.url = url.rstrip("/")
        self.collection = collection

    def health(self) -> dict:
        import requests

        response = requests.get(f"{self.url}/collections/{self.collection}", timeout=3)
        return {"available": response.status_code < 500, "status_code": response.status_code}
