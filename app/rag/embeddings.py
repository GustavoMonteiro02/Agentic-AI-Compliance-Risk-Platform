from __future__ import annotations

import hashlib
import math
import re
import time
from typing import Protocol

import requests


TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]+")


class EmbeddingProvider(Protocol):
    dimensions: int
    provider_name: str

    def embed(self, text: str) -> list[float]:
        ...

    def embed_many(self, texts: list[str]) -> list[list[float]]:
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
        return self.embed_many([text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
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
        timeout_seconds: int = 30,
        max_retries: int = 3,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.dimensions = dimensions
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.provider_name = "openai"

    def embed(self, text: str) -> list[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._request_with_retries({"model": self.model, "input": texts})
        vectors = [item["embedding"] for item in response.json()["data"]]
        if vectors and len(vectors[0]) != self.dimensions:
            self.dimensions = len(vectors[0])
        return vectors

    def _request_with_retries(self, payload: dict) -> requests.Response:
        last_response: requests.Response | None = None
        for attempt in range(self.max_retries + 1):
            response = requests.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout_seconds,
            )
            if response.status_code < 400:
                return response
            last_response = response
            if response.status_code not in {429, 500, 502, 503, 504} or attempt >= self.max_retries:
                response.raise_for_status()
            time.sleep(_retry_delay_seconds(response, attempt))
        if last_response is not None:
            last_response.raise_for_status()
        raise RuntimeError("OpenAI embedding request failed before receiving a response.")


def _retry_delay_seconds(response: requests.Response, attempt: int) -> float:
    retry_after = response.headers.get("retry-after")
    if retry_after:
        try:
            return min(float(retry_after), 30.0)
        except ValueError:
            pass
    return min(2.0 * (attempt + 1), 30.0)


def build_embedding_provider(settings) -> EmbeddingProvider:
    if settings.embedding_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")
        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
            dimensions=settings.embedding_dimensions,
            timeout_seconds=settings.openai_timeout_seconds,
            max_retries=settings.openai_max_retries,
        )
    return LocalHashEmbeddingProvider(settings.embedding_dimensions)
