from pathlib import Path

from app.rag.chunker import parse_markdown_requirements
from app.rag.vector_store import LocalVectorStore


def ingest_markdown_directory(base_path: Path) -> LocalVectorStore:
    store = LocalVectorStore()
    for path in sorted(base_path.glob("**/*.md")):
        chunks = parse_markdown_requirements(path.relative_to(base_path).as_posix(), path.read_text(encoding="utf-8"))
        store.add(chunks)
    return store


def ingest_summary(base_path: Path) -> dict:
    store = ingest_markdown_directory(base_path)
    return {"chunk_count": store.count(), "sources": store.sources()}
