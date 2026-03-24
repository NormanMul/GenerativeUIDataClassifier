"""UDC ContextVault — Post-session memory extractor.

Analyses a completed session's conversation history to extract
long-term memory entries that are persisted in the virtual filesystem
for future retrieval.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)


class MemoryExtractor:
    """Extract long-term memories from a completed conversation session.

    After a session is closed this extractor reviews the full message
    history and produces structured memory entries — facts, preferences,
    decisions, and action items — that are stored in the ``user/`` or
    ``agent/`` namespace of the virtual filesystem.
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

    async def extract(self, session: dict[str, Any]) -> list[dict[str, Any]]:
        """Run memory extraction on a closed session.

        Uses Azure OpenAI to analyse the conversation and return
        structured memory entries.
        """
        messages = session.get("messages", [])
        if not messages:
            return []

        session_id = session.get("session_id", "unknown")
        conversation = "\n".join(
            f"{m.get('role', 'unknown')}: {m.get('content', '')}" for m in messages
        )

        system_prompt = (
            "You are a memory extraction engine. Given a conversation, extract key facts, "
            "decisions, and action items. Return a JSON array where each element has: "
            '"fact" (string), "category" (one of "preference", "decision", "action_item", "context"), '
            'and "confidence" (float 0-1). Return ONLY the JSON array, no other text.'
        )

        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": conversation},
            ],
            "max_tokens": 1024,
            "temperature": 0.2,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(self._url(), json=payload, headers=self._headers())
                resp.raise_for_status()

            raw = resp.json()["choices"][0]["message"]["content"].strip()
            # Strip markdown code fences if present.
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            memories: list[dict[str, Any]] = json.loads(raw)
        except (httpx.HTTPError, json.JSONDecodeError, KeyError) as exc:
            logger.warning("memory_extractor.llm_failed", error=str(exc))
            # Fallback: heuristic extraction.
            memories = self._heuristic_extract(messages)

        # Attach source session to each memory.
        for mem in memories:
            mem["source_session"] = session_id

        logger.info("memory_extractor.done", session_id=session_id, count=len(memories))
        return memories

    @staticmethod
    def _heuristic_extract(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Fallback heuristic extraction when the LLM is unavailable."""
        memories: list[dict[str, Any]] = []
        for msg in messages:
            content = msg.get("content", "")
            lower = content.lower()
            if any(kw in lower for kw in ("decided", "decision", "agreed", "confirmed")):
                memories.append({"fact": content[:300], "category": "decision", "confidence": 0.7})
            elif any(kw in lower for kw in ("todo", "action item", "need to", "must")):
                memories.append({"fact": content[:300], "category": "action_item", "confidence": 0.65})
            elif any(kw in lower for kw in ("prefer", "like", "always", "never", "want")):
                memories.append({"fact": content[:300], "category": "preference", "confidence": 0.7})
        return memories
