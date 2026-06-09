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

