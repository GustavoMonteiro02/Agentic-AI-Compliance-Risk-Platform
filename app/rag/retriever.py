from pathlib import Path
import re
from typing import Any

from app.config import get_settings
from app.rag.chunker import DocumentChunk, parse_markdown_requirements
from app.rag.embeddings import build_embedding_provider
from app.rag.vector_store import QdrantVectorStore


TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]+")


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(text)}


def _phrases(query: str) -> set[str]:
    words = [token.lower() for token in TOKEN_RE.findall(query)]
    phrases = {" ".join(words[index : index + 2]) for index in range(max(len(words) - 1, 0))}
    if len(words) >= 3:
        phrases.add(" ".join(words))
    return {phrase for phrase in phrases if phrase}


def _weighted_overlap(query_tokens: set[str], field_text: str, weight: float) -> float:
    if not query_tokens:
        return 0
    return len(query_tokens & _tokens(field_text)) * weight


def _phrase_score(query_phrases: set[str], text: str) -> float:
    lowered = text.lower()
    return sum(1.0 for phrase in query_phrases if phrase in lowered)


def _metadata_score(query_tokens: set[str], query: str, chunk: DocumentChunk) -> float:
    haystack = " ".join(
        [
            chunk.category,
            chunk.document_type,
            chunk.jurisdiction,
            chunk.authority,
            " ".join(chunk.tags),
            chunk.title,
        ]
    ).lower()
    score = len(query_tokens & _tokens(haystack)) * 0.9

    query_lower = query.lower()
    boost_rules = [
        ({"employment", "hr", "candidate", "recruitment"}, {"employment", "human oversight", "bias"}, 1.4),
        ({"personal", "data", "privacy", "gdpr"}, {"data protection", "privacy", "gdpr"}, 1.5),
        ({"security", "resilience", "incident", "dora", "nis2"}, {"security", "resilience", "incident"}, 1.4),
        ({"oversight", "human", "review"}, {"human oversight", "review"}, 1.2),
        ({"logging", "audit", "traceability"}, {"audit logging", "traceability"}, 1.1),
        ({"prompt", "injection", "red-team", "red"}, {"prompt injection", "security testing"}, 1.2),
    ]
    for query_terms, chunk_terms, boost in boost_rules:
        query_match = query_tokens & query_terms or any(term in query_lower for term in query_terms)
        chunk_match = any(term in haystack for term in chunk_terms)
        if query_match and chunk_match:
            score += boost
    return score


def _source_quality(chunk: DocumentChunk) -> float:
    score = 0.0
    if chunk.document_type in {"regulation", "directive"}:
        score += 0.5
    elif chunk.document_type in {"policy", "control"}:
        score += 0.3
    if chunk.authority:
        score += 0.2
    if chunk.source_url:
        score += 0.2
    return score


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

    def _diversified_top_k(
        self,
        scored: list[tuple[float, DocumentChunk, dict[str, float]]],
        top_k: int,
    ) -> list[tuple[float, DocumentChunk, dict[str, float]]]:
        selected: list[tuple[float, DocumentChunk, dict[str, float]]] = []
        category_counts: dict[str, int] = {}
        for item in scored:
            category = item[1].category
            if category_counts.get(category, 0) >= 1:
                continue
            selected.append(item)
            category_counts[category] = category_counts.get(category, 0) + 1
            if len(selected) == top_k:
                return selected

        selected_ids = {id(item[1]) for item in selected}
        for item in scored:
            if id(item[1]) in selected_ids:
                continue
            selected.append(item)
            if len(selected) == top_k:
                break
        return selected

    def _qdrant_scores(self, settings: Any, query: str, limit: int) -> tuple[dict[str, float], dict[str, Any]]:
        if settings.vector_db != "qdrant":
            return {}, {"available": False}

        qdrant = QdrantVectorStore(
            settings.qdrant_url,
            settings.qdrant_collection,
            build_embedding_provider(settings),
        )
        try:
            health = qdrant.health()
            if not health.get("available"):
                return {}, health
            results = qdrant.search(query, limit=limit)
        except Exception as exc:
            return {}, {"available": False, "error": str(exc)}

        scores = {
            result.get("payload", {}).get("requirement_id"): float(result.get("score") or 0)
            for result in results
            if result.get("payload", {}).get("requirement_id")
        }
        return scores, {"available": True, "result_count": len(scores)}

    def search(self, query: str, top_k: int = 6) -> list[dict[str, Any]]:
        settings = get_settings()
        vector_scores, health = self._qdrant_scores(settings, query, limit=max(top_k * 3, 12))
        query_tokens = _tokens(query)
        query_phrases = _phrases(query)
        scored = []
        for chunk in self.load():
            vector_score = vector_scores.get(chunk.requirement_id, 0.0)
            lexical_score = (
                _weighted_overlap(query_tokens, chunk.title, 3.0)
                + _weighted_overlap(query_tokens, chunk.category, 2.5)
                + _weighted_overlap(query_tokens, " ".join(chunk.tags), 2.0)
                + _weighted_overlap(query_tokens, chunk.source, 1.2)
                + _weighted_overlap(query_tokens, chunk.authority, 1.2)
                + _weighted_overlap(query_tokens, chunk.text, 1.0)
            )
            phrase_score = _phrase_score(
                query_phrases,
                f"{chunk.title} {chunk.category} {' '.join(chunk.tags)} {chunk.text}",
            )
            metadata_score = _metadata_score(query_tokens, query, chunk)
            source_quality = _source_quality(chunk)
            final_score = lexical_score + (phrase_score * 1.4) + metadata_score + source_quality + (vector_score * 8)
            if final_score:
                scored.append(
                    (
                        final_score,
                        chunk,
                        {
                            "lexical": round(lexical_score, 3),
                            "phrase": round(phrase_score, 3),
                            "metadata": round(metadata_score, 3),
                            "source_quality": round(source_quality, 3),
                            "vector": round(vector_score, 3),
                            "final": round(final_score, 3),
                        },
                    )
                )
        scored.sort(key=lambda item: (item[0], item[1].document_type == "regulation"), reverse=True)
        reranked = self._diversified_top_k(scored, top_k)
        retriever_mode = "local-hybrid-rerank"
        if health.get("available"):
            retriever_mode = "local-hybrid-rerank-qdrant-ready"
        return [
            {
                "requirement_id": chunk.requirement_id,
                "title": chunk.title,
                "source": chunk.source,
                "category": chunk.category,
                "source_url": chunk.source_url,
                "jurisdiction": chunk.jurisdiction,
                "document_type": chunk.document_type,
                "authority": chunk.authority,
                "tags": list(chunk.tags),
                "summary": chunk.text,
                "relevance": "high" if score >= 6 else "medium",
                "retriever": retriever_mode,
                "score": round(score, 3),
                "score_breakdown": breakdown,
                "metadata": chunk.metadata,
                "citation": {
                    "label": f"{chunk.authority}: {chunk.title}",
                    "source": chunk.source,
                    "source_url": chunk.source_url,
                    "requirement_id": chunk.requirement_id,
                },
            }
            for score, chunk, breakdown in reranked
        ]
