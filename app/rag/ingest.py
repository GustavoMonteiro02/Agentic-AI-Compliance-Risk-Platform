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
        chunks = parse_markdown_requirements(source["local_path"], local_path.read_text(encoding="utf-8")) if local_path.exists() else []
        locators = sorted({chunk.locator for chunk in chunks if chunk.locator})
        required_locators = source.get("minimum_required_locators") or []
        missing_required_locators = sorted(set(required_locators) - set(locators))
        expected_article_count = source.get("expected_article_count")
        coverage_percent = (
            round((len(locators) / expected_article_count) * 100, 2)
            if expected_article_count
            else None
        )
        sources.append(
            {
                **source,
                "available": local_path.exists(),
                "chunk_count": len(chunks),
                "parsed_locators": locators,
                "missing_required_locators": missing_required_locators,
                "coverage_percent": coverage_percent,
                "content_hashes": sorted({chunk.content_hash for chunk in chunks if chunk.content_hash}),
                "readiness": _source_readiness(
                    available=local_path.exists(),
                    chunk_count=len(chunks),
                    ingestion_status=source.get("ingestion_status"),
                    missing_required_locators=missing_required_locators,
                    expected_article_count=expected_article_count,
                    locator_count=len(locators),
                ),
            }
        )
    return {"manifest": manifest.get("version"), "sources": sources, "validation": validate_legal_sources(sources)}


def _source_readiness(
    *,
    available: bool,
    chunk_count: int,
    ingestion_status: str | None,
    missing_required_locators: list[str],
    expected_article_count: int | None,
    locator_count: int,
) -> dict:
    blockers: list[str] = []
    warnings: list[str] = []
    next_actions: list[str] = []

    if not available:
        blockers.append("local_path_missing")
        next_actions.append("Add the official source file at local_path.")
    if available and chunk_count == 0:
        blockers.append("no_article_chunks")
        next_actions.append("Convert the source into article-level Markdown sections.")
    if missing_required_locators:
        blockers.append("required_locators_missing")
        next_actions.append("Add required locators: " + ", ".join(missing_required_locators))
    if ingestion_status != "available":
        warnings.append(f"ingestion_status:{ingestion_status or 'missing'}")
        next_actions.append("Set ingestion_status to available only after full official-source ingestion.")
    if expected_article_count and locator_count < expected_article_count:
        warnings.append("partial_article_coverage")
        next_actions.append(f"Add remaining article locators until coverage reaches {expected_article_count}.")

    return {
        "ready": not blockers and not warnings,
        "blockers": blockers,
        "warnings": warnings,
        "next_actions": next_actions,
    }


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
        if source.get("missing_required_locators"):
            errors.append(f"{source_id}: missing required locators {', '.join(source['missing_required_locators'])}")
        expected_article_count = source.get("expected_article_count")
        if expected_article_count and source.get("chunk_count", 0) < expected_article_count:
            warnings.append(
                f"{source_id}: parsed {source.get('chunk_count', 0)}/{expected_article_count} expected article-level chunks"
            )

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
