from __future__ import annotations

import hashlib
import math
import re


TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]+")


class LocalHashEmbeddingProvider:
    """Deterministic local embeddings for offline development and tests.

    The vector is intentionally simple: tokens are hashed into a fixed-size
    bag-of-words vector and L2-normalized. Production deployments can replace
    this provider with a managed embeddings model while keeping the vector-store
    contract stable.
    """

    def __init__(self, dimensions: int = 128) -> None:
        self.dimensions = dimensions

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
