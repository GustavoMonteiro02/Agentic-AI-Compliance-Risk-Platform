from app.rag.chunker import DocumentChunk
from app.rag.embeddings import EmbeddingProvider, LocalHashEmbeddingProvider


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

    def chunks(self) -> list[DocumentChunk]:
        return list(self._chunks)


class QdrantVectorStore:
    """Small Qdrant adapter for persistent requirement retrieval."""

    def __init__(
        self,
        url: str,
        collection: str,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self.url = url.rstrip("/")
        self.collection = collection
        self.embedding_provider = embedding_provider or LocalHashEmbeddingProvider()
        self.dimensions = self.embedding_provider.dimensions

    def health(self) -> dict:
        import requests

        response = requests.get(f"{self.url}/collections/{self.collection}", timeout=3)
        return {"available": response.status_code < 500, "status_code": response.status_code}

    def ensure_collection(self) -> dict:
        import requests

        response = requests.put(
            f"{self.url}/collections/{self.collection}",
            json={"vectors": {"size": self.dimensions, "distance": "Cosine"}},
            timeout=5,
        )
        return {"ok": response.status_code < 400, "status_code": response.status_code}

    def upsert(self, chunks: list[DocumentChunk]) -> dict:
        import requests

        self.ensure_collection()
        points = [
            {
                "id": self._point_id(chunk),
                "vector": self.embedding_provider.embed(self._embedding_text(chunk)),
                "payload": self._payload(chunk),
            }
            for chunk in chunks
        ]
        response = requests.put(
            f"{self.url}/collections/{self.collection}/points",
            params={"wait": "true"},
            json={"points": points},
            timeout=10,
        )
        return {"ok": response.status_code < 400, "status_code": response.status_code, "point_count": len(points)}

    def search(self, query: str, limit: int = 12) -> list[dict]:
        import requests

        response = requests.post(
            f"{self.url}/collections/{self.collection}/points/search",
            json={
                "vector": self.embedding_provider.embed(query),
                "limit": limit,
                "with_payload": True,
            },
            timeout=5,
        )
        response.raise_for_status()
        return response.json().get("result", [])

    def _embedding_text(self, chunk: DocumentChunk) -> str:
        return " ".join(
            [
                chunk.title,
                chunk.category,
                chunk.text,
                chunk.jurisdiction,
                chunk.document_type,
                chunk.authority,
                " ".join(chunk.tags),
            ]
        )

    def _point_id(self, chunk: DocumentChunk) -> str:
        import hashlib

        stable_key = f"{chunk.source}:{chunk.requirement_id}"
        return hashlib.md5(stable_key.encode("utf-8")).hexdigest()

    def _payload(self, chunk: DocumentChunk) -> dict:
        return {
            "requirement_id": chunk.requirement_id,
            "title": chunk.title,
            "source": chunk.source,
            "category": chunk.category,
            "summary": chunk.text,
            "jurisdiction": chunk.jurisdiction,
            "document_type": chunk.document_type,
            "authority": chunk.authority,
            "source_url": chunk.source_url,
            "effective_date": chunk.effective_date,
            "locator": chunk.locator,
            "content_hash": chunk.content_hash,
            "tags": list(chunk.tags),
            "metadata": chunk.metadata,
            "embedding_provider": self.embedding_provider.provider_name,
            "citation": {
                "label": f"{chunk.authority}: {chunk.title}",
                "source_url": chunk.source_url,
                "source": chunk.source,
                "requirement_id": chunk.requirement_id,
            },
        }
