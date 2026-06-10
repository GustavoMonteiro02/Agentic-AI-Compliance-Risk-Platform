from pathlib import Path

from app.config import get_settings
from app.rag.chunker import parse_markdown_requirements
from app.rag.embeddings import build_embedding_provider
from app.rag.vector_store import LocalVectorStore
from app.rag.vector_store import QdrantVectorStore


def ingest_markdown_directory(base_path: Path) -> LocalVectorStore:
    store = LocalVectorStore()
    for path in sorted(base_path.glob("**/*.md")):
        chunks = parse_markdown_requirements(path.relative_to(base_path).as_posix(), path.read_text(encoding="utf-8"))
        store.add(chunks)
    return store


def ingest_summary(base_path: Path) -> dict:
    store = ingest_markdown_directory(base_path)
    return {"chunk_count": store.count(), "sources": store.sources()}


def ingest_qdrant(base_path: Path) -> dict:
    settings = get_settings()
    store = ingest_markdown_directory(base_path)
    qdrant = QdrantVectorStore(
        settings.qdrant_url,
        settings.qdrant_collection,
        build_embedding_provider(settings),
    )
    result = qdrant.upsert(store.chunks())
    return {
        "chunk_count": store.count(),
        "sources": store.sources(),
        "vector_db": "qdrant",
        "collection": settings.qdrant_collection,
        "embedding_provider": settings.embedding_provider,
        "embedding_model": settings.openai_embedding_model if settings.embedding_provider == "openai" else "local_hash",
        **result,
    }
