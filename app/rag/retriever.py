from pathlib import Path
from dataclasses import dataclass, field
import re
from typing import Any

from app.config import get_settings
from app.rag.chunker import DocumentChunk, parse_markdown_requirements
from app.rag.embeddings import build_embedding_provider
from app.rag.vector_store import QdrantVectorStore


TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "for",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}
QUERY_EXPANSIONS = {
    "hr": {"employment", "candidate", "recruitment", "human oversight", "bias"},
    "candidate": {"employment", "recruitment", "human oversight", "bias"},
    "cv": {"employment", "candidate", "recruitment", "personal data"},
    "privacy": {"gdpr", "personal data", "data protection", "lawful basis"},
    "pii": {"personal data", "data protection", "gdpr"},
    "incident": {"security", "resilience", "dora", "nis2", "audit logging"},
    "cyber": {"security", "resilience", "incident", "nis2"},
    "agent": {"tool use", "prompt injection", "security testing", "audit logging"},
    "rag": {"retrieval", "prompt injection", "data leakage", "security testing"},
    "oversight": {"human review", "intervention", "monitoring"},
    "article": {"regulation", "legal source", "locator"},
}


@dataclass(frozen=True)
class RetrievalFilters:
    jurisdictions: set[str] = field(default_factory=set)
    document_types: set[str] = field(default_factory=set)
    categories: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    authorities: set[str] = field(default_factory=set)

    @classmethod
    def from_values(
        cls,
        *,
        jurisdiction: str | None = None,
        document_type: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        authority: str | None = None,
    ) -> "RetrievalFilters":
        return cls(
            jurisdictions=_normalize_filter_values(jurisdiction),
            document_types=_normalize_filter_values(document_type),
            categories=_normalize_filter_values(category),
            tags=_normalize_filter_values(tags or []),
            authorities=_normalize_filter_values(authority),
        )

    @property
    def active(self) -> bool:
        return any([self.jurisdictions, self.document_types, self.categories, self.tags, self.authorities])


def _normalize_filter_values(value: str | list[str] | None) -> set[str]:
    if value is None:
        return set()
    values = value if isinstance(value, list) else value.split(",")
    return {item.strip().lower() for item in values if item and item.strip()}


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(text) if token.lower() not in STOPWORDS}


def _expanded_query_text(query: str) -> str:
    tokens = _tokens(query)
    expansions = set()
    for token in tokens:
        expansions.update(QUERY_EXPANSIONS.get(token, set()))
    return " ".join([query, *sorted(expansions)])


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
            chunk.locator or "",
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


def _matches_filters(chunk: DocumentChunk, filters: RetrievalFilters | None) -> bool:
    if not filters or not filters.active:
        return True
    if filters.jurisdictions and chunk.jurisdiction.lower() not in filters.jurisdictions:
        return False
    if filters.document_types and chunk.document_type.lower() not in filters.document_types:
        return False
    if filters.categories and chunk.category.lower() not in filters.categories:
        return False
    if filters.authorities and chunk.authority.lower() not in filters.authorities:
        return False
    if filters.tags and not filters.tags.intersection({tag.lower() for tag in chunk.tags}):
        return False
    return True


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

    def search(
        self,
        query: str,
        top_k: int = 6,
        filters: RetrievalFilters | None = None,
    ) -> list[dict[str, Any]]:
        settings = get_settings()
        vector_scores, health = self._qdrant_scores(settings, query, limit=max(top_k * 3, 12))
        expanded_query = _expanded_query_text(query)
        query_tokens = _tokens(expanded_query)
        query_phrases = _phrases(expanded_query)
        scored = []
        for chunk in self.load():
            if not _matches_filters(chunk, filters):
                continue
            vector_score = vector_scores.get(chunk.requirement_id, 0.0)
            lexical_score = (
                _weighted_overlap(query_tokens, chunk.title, 3.0)
                + _weighted_overlap(query_tokens, chunk.category, 2.5)
                + _weighted_overlap(query_tokens, " ".join(chunk.tags), 2.0)
                + _weighted_overlap(query_tokens, chunk.source, 1.2)
                + _weighted_overlap(query_tokens, chunk.authority, 1.2)
                + _weighted_overlap(query_tokens, chunk.locator or "", 2.5)
                + _weighted_overlap(query_tokens, chunk.text, 1.0)
            )
            phrase_score = _phrase_score(
                query_phrases,
                f"{chunk.title} {chunk.category} {chunk.locator or ''} {' '.join(chunk.tags)} {chunk.text}",
            )
            metadata_score = _metadata_score(query_tokens, expanded_query, chunk)
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
                "locator": chunk.locator,
                "content_hash": chunk.content_hash,
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
                    "locator": chunk.locator,
                },
            }
            for score, chunk, breakdown in reranked
        ]
