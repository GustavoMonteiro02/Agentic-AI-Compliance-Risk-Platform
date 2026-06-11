from pathlib import Path
import json

from app.config import get_settings
from app.rag.chunker import parse_markdown_requirements
from app.rag.embeddings import build_embedding_provider
from app.rag.vector_store import LocalVectorStore
from app.rag.vector_store import PineconeVectorStore
from app.rag.vector_store import QdrantVectorStore


def ingest_markdown_directory(base_path: Path) -> LocalVectorStore:
    store = LocalVectorStore()
    for path in sorted(base_path.glob("**/*.md")):
        chunks = parse_markdown_requirements(path.relative_to(base_path).as_posix(), path.read_text(encoding="utf-8"))
        store.add(chunks)
    return store


def ingest_summary(base_path: Path) -> dict:
    store = ingest_markdown_directory(base_path)
    return {
        "chunk_count": store.count(),
        "sources": store.sources(),
        "legal_sources": legal_source_summary(base_path),
    }


def legal_source_summary(base_path: Path) -> dict:
    manifest_path = base_path / "legal_sources_manifest.json"
    if not manifest_path.exists():
        return {"manifest": None, "sources": [], "validation": {"ready": False, "errors": ["manifest_missing"], "warnings": []}}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sources = []
    for source in manifest.get("sources", []):
        local_path = base_path / source["local_path"]
        sources.append(
            {
                **source,
                "available": local_path.exists(),
                "chunk_count": len(parse_markdown_requirements(source["local_path"], local_path.read_text(encoding="utf-8")))
                if local_path.exists()
                else 0,
            }
        )
    return {"manifest": manifest.get("version"), "sources": sources, "validation": validate_legal_sources(sources)}


def validate_legal_sources(sources: list[dict]) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    required_fields = {"id", "title", "jurisdiction", "authority", "source_url", "document_type", "local_path"}

    for source in sources:
        source_id = source.get("id", "unknown")
        missing = sorted(field for field in required_fields if not source.get(field))
        if missing:
            errors.append(f"{source_id}: missing required fields {', '.join(missing)}")
        if not source.get("available"):
            errors.append(f"{source_id}: local_path not found")
            continue
        if source.get("chunk_count", 0) == 0:
            errors.append(f"{source_id}: no article-level chunks parsed")
        status = source.get("ingestion_status")
        if status != "available":
            warnings.append(f"{source_id}: ingestion_status is {status}")
        if status == "sample_extract":
            warnings.append(f"{source_id}: sample extract is not production full-text corpus")

    return {"ready": not errors and not warnings, "errors": errors, "warnings": warnings}


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


def ingest_pinecone(base_path: Path) -> dict:
    settings = get_settings()
    if not settings.pinecone_api_key or not settings.pinecone_index_host:
        raise ValueError("PINECONE_API_KEY and PINECONE_INDEX_HOST are required for Pinecone ingestion")
    store = ingest_markdown_directory(base_path)
    pinecone = PineconeVectorStore(
        settings.pinecone_api_key,
        settings.pinecone_index_host,
        settings.pinecone_namespace,
        build_embedding_provider(settings),
    )
    result = pinecone.upsert(store.chunks())
    return {
        "chunk_count": store.count(),
        "sources": store.sources(),
        "vector_db": "pinecone",
        "namespace": settings.pinecone_namespace,
        "embedding_provider": settings.embedding_provider,
        "embedding_model": settings.openai_embedding_model if settings.embedding_provider == "openai" else "local_hash",
        **result,
    }
