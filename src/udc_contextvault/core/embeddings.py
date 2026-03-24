"""UDC ContextVault — Embedding service backed by Azure OpenAI.

Wraps the Azure OpenAI ``text-embedding-3-small`` model to produce
vector representations of context entries for similarity search.
"""

from __future__ import annotations

import os

import httpx
import structlog

logger = structlog.get_logger(__name__)

DEFAULT_MODEL = "text-embedding-3-small"


class EmbeddingService:
    """Generate text embeddings via Azure OpenAI.

    Attributes:
        model: The deployment name / model identifier to use.
    """

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self.model = model
        self._endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
        self._deployment = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", model)
        self._api_key = os.environ.get("AZURE_OPENAI_API_KEY", "")
        self._api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01")

    def _url(self) -> str:
        return (
            f"{self._endpoint}/openai/deployments/{self._deployment}"
            f"/embeddings?api-version={self._api_version}"
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "api-key": self._api_key,
        }

    async def embed_text(self, text: str) -> list[float]:
        """Produce an embedding vector for a single text string."""
        vectors = await self.embed_batch([text])
        return vectors[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Produce embedding vectors for a batch of texts."""
        if not texts:
            return []

        payload = {"input": texts, "model": self._deployment}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self._url(), json=payload, headers=self._headers())
            response.raise_for_status()

        data = response.json()
        # Azure OpenAI returns {"data": [{"embedding": [...], "index": 0}, ...]}
        sorted_items = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in sorted_items]
