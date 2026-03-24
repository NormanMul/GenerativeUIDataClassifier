"""UDC ContextVault — Context layer definitions and compression.

Defines three fidelity tiers for stored context:

* **L0** — headline / title  (≤ 30 tokens)
* **L1** — summary            (≤ 200 tokens)
* **L2** — full content        (original)

The ``LayerCompressor`` generates L0 and L1 representations from the
original L2 content using an LLM summarisation pipeline.
"""

from __future__ import annotations

import enum
import os

import httpx
import structlog

logger = structlog.get_logger(__name__)


class ContextLayer(enum.Enum):
    """Fidelity tier for a stored context entry."""

    L0 = "l0"  # headline / title
    L1 = "l1"  # summary
    L2 = "l2"  # full content


class LayerCompressor:
    """Generate multi-layer compressed representations of context content.

    Given the full L2 text, produces L1 (summary) and L0 (headline)
    variants suitable for constrained token budgets.
    """

    def __init__(self) -> None:
        self._endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
        self._deployment = os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o")
        self._api_key = os.environ.get("AZURE_OPENAI_API_KEY", "")
        self._api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01")

    def _url(self) -> str:
        return (
            f"{self._endpoint}/openai/deployments/{self._deployment}"
            f"/chat/completions?api-version={self._api_version}"
        )

    def _headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json", "api-key": self._api_key}

    async def _chat(self, system_prompt: str, user_content: str, max_tokens: int) -> str:
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(self._url(), json=payload, headers=self._headers())
            resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    async def compress_to_l1(self, content: str) -> str:
        """Compress full content into a concise summary (L1, ~200 tokens)."""
        return await self._chat(
            system_prompt=(
                "You are a concise summariser. Produce a summary of approximately "
                "200 tokens that preserves all key facts, entities, and decisions."
            ),
            user_content=content,
            max_tokens=250,
        )

    async def compress_to_l0(self, content: str) -> str:
        """Compress full content into a headline (L0, ~30 tokens)."""
        return await self._chat(
            system_prompt=(
                "You are a headline writer. Produce a single-sentence headline of "
                "at most 30 tokens that captures the core topic."
            ),
            user_content=content,
            max_tokens=40,
        )

    async def generate_layers(self, content: str) -> dict[str, str]:
        """Produce all three compression layers from the original content."""
        l1 = await self.compress_to_l1(content)
        l0 = await self.compress_to_l0(content)
        return {
            "l0": l0,
            "l1": l1,
            "l2": content,
        }
