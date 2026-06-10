from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

import requests


TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]+")


class EmbeddingProvider(Protocol):
    dimensions: int
    provider_name: str

    def embed(self, text: str) -> list[float]:
        ...


class LocalHashEmbeddingProvider:
    """Deterministic local embeddings for offline development and tests.

    The vector is intentionally simple: tokens are hashed into a fixed-size
    bag-of-words vector and L2-normalized. Production deployments can replace
    this provider with a managed embeddings model while keeping the vector-store
    contract stable.
    """

    def __init__(self, dimensions: int = 128) -> None:
        self.dimensions = dimensions
        self.provider_name = "local_hash"

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in TOKEN_RE.findall(text.lower()):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return vector
        return [round(value / magnitude, 6) for value in vector]


class OpenAIEmbeddingProvider:
    """Managed OpenAI embedding provider for production vector search."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.dimensions = dimensions
        self.provider_name = "openai"

    def embed(self, text: str) -> list[float]:
        response = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={"model": self.model, "input": text},
            timeout=30,
        )
        response.raise_for_status()
        vector = response.json()["data"][0]["embedding"]
        if len(vector) != self.dimensions:
            self.dimensions = len(vector)
        return vector


def build_embedding_provider(settings) -> EmbeddingProvider:
    if settings.embedding_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")
        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
            dimensions=settings.embedding_dimensions,
        )
    return LocalHashEmbeddingProvider(settings.embedding_dimensions)
