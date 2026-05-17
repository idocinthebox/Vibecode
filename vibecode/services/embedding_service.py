from __future__ import annotations

from typing import Any


class EmbeddingService:
    """Stub embedding service for optional pgvector support.

    To enable real embeddings, inject an OpenAI, Cohere, or local model client.
    """

    def __init__(self, provider: str = "none", model: str = "none") -> None:
        self.provider = provider
        self.model = model

    def embed(self, text: str) -> list[float] | None:
        return None

    def is_available(self) -> bool:
        return False
