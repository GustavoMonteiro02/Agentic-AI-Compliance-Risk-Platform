from pathlib import Path
import re

from app.config import get_settings
from app.rag.chunker import DocumentChunk, parse_markdown_requirements


TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]+")


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(text)}


class LocalComplianceRetriever:
    def __init__(self, base_path: Path | None = None) -> None:
        self.base_path = base_path or get_settings().knowledge_base_path
        self._chunks: list[DocumentChunk] | None = None

    def load(self) -> list[DocumentChunk]:
        if self._chunks is not None:
            return self._chunks
        chunks: list[DocumentChunk] = []
        for path in sorted(self.base_path.glob("**/*.md")):
            relative = path.relative_to(self.base_path).as_posix()
            chunks.extend(parse_markdown_requirements(relative, path.read_text(encoding="utf-8")))
        self._chunks = chunks
        return chunks

    def search(self, query: str, top_k: int = 6) -> list[dict[str, str]]:
        query_tokens = _tokens(query)
        scored = []
        for chunk in self.load():
            text_tokens = _tokens(f"{chunk.title} {chunk.category} {chunk.text}")
            overlap = len(query_tokens & text_tokens)
            bonus = 2 if chunk.category in query_tokens else 0
            score = overlap + bonus
            if score:
                scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "requirement_id": chunk.requirement_id,
                "title": chunk.title,
                "source": chunk.source,
                "summary": chunk.text,
                "relevance": "high" if score >= 4 else "medium",
            }
            for score, chunk in scored[:top_k]
        ]

