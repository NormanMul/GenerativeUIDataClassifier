"""UDC ContextVault — Conversation history management.

Provides retrieval and compaction of per-session conversation turns
so that older messages can be compressed while recent turns remain
at full fidelity.
"""

from __future__ import annotations

import json
from typing import Any

import structlog

from udc_contextvault.core.layers import LayerCompressor
from udc_contextvault.storage.cache import RedisContextCache

logger = structlog.get_logger(__name__)


class ConversationHistory:
    """Manage and compact conversation turn history for a session.

    Keeps the most recent *max_turns* at full fidelity (L2) while
    compressing older turns into summary form (L1 / L0) to keep
    the overall token budget within bounds.
    """

    def __init__(
        self,
        cache: RedisContextCache | None = None,
        compressor: LayerCompressor | None = None,
    ) -> None:
        self._cache = cache or RedisContextCache()
        self._compressor = compressor or LayerCompressor()

    def _list_key(self, session_id: str) -> str:
        return f"history:{session_id}"

    async def append(self, session_id: str, role: str, content: str) -> None:
        """Add a message to session history (stored in a Redis list)."""
        entry = json.dumps({"role": role, "content": content, "layer": "l2"})
        await self._cache._redis.rpush(self._list_key(session_id), entry)

    async def get_history(
        self,
        session_id: str,
        max_turns: int = 50,
    ) -> list[dict[str, Any]]:
        """Retrieve conversation history for a session.

        Returns the last *max_turns* messages at full fidelity.
        Older messages may already be in compressed (L1) form.
        """
        raw_items = await self._cache._redis.lrange(self._list_key(session_id), 0, -1)
        messages: list[dict[str, Any]] = []
        for raw in raw_items:
            try:
                messages.append(json.loads(raw))
            except (json.JSONDecodeError, TypeError):
                messages.append({"role": "unknown", "content": str(raw), "layer": "l2"})

        # Return all stored messages, but only the most recent max_turns are
        # guaranteed to be at full L2 fidelity.
        return messages[-max_turns:] if len(messages) > max_turns else messages

    async def compact(self, session_id: str, keep_recent: int = 20) -> None:
        """Compress older conversation turns to free token budget.

        Turns older than *keep_recent* are replaced with L1 summaries.
        """
        key = self._list_key(session_id)
        raw_items = await self._cache._redis.lrange(key, 0, -1)

        if len(raw_items) <= keep_recent:
            return  # Nothing to compact.

        older = raw_items[: len(raw_items) - keep_recent]
        recent = raw_items[len(raw_items) - keep_recent :]

        # Batch-compress older messages.
        compacted: list[str] = []
        for raw in older:
            try:
                msg = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                compacted.append(raw)
                continue

            if msg.get("layer") != "l2":
                compacted.append(raw)
                continue

            content = msg.get("content", "")
            if len(content) > 200:
                summary = await self._compressor.compress_to_l1(content)
                msg["content"] = summary
                msg["layer"] = "l1"
            compacted.append(json.dumps(msg))

        # Rewrite the list atomically.
        pipe = self._cache._redis.pipeline()
        pipe.delete(key)
        for item in compacted + list(recent):
            pipe.rpush(key, item)
        await pipe.execute()

        logger.info("history.compact", session_id=session_id, compacted=len(compacted), kept=len(recent))

    async def clear(self, session_id: str) -> None:
        """Clear history for a session."""
        await self._cache._redis.delete(self._list_key(session_id))
