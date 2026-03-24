"""UDC ContextVault — Session lifecycle manager.

Manages the full lifecycle of a conversation session: creation,
message accumulation, and graceful close with memory extraction.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from udc_contextvault.session.memory_extractor import MemoryExtractor
from udc_contextvault.storage.cache import RedisContextCache

logger = structlog.get_logger(__name__)

DEFAULT_TTL = 3600  # 1 hour


class SessionManager:
    """Orchestrate conversation session lifecycle.

    A session tracks a single conversation between a user (or agent)
    and the system.  On close the accumulated messages are passed
    through memory extraction so that key facts persist beyond the
    session's lifetime.
    """

    def __init__(
        self,
        cache: RedisContextCache | None = None,
        memory_extractor: MemoryExtractor | None = None,
    ) -> None:
        self._cache = cache or RedisContextCache()
        self._memory_extractor = memory_extractor or MemoryExtractor()

    def _key(self, session_id: str) -> str:
        return f"session:{session_id}"

    async def create_session(
        self,
        user_id: str,
        role: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new conversation session stored in Redis."""
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        session: dict[str, Any] = {
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "metadata": metadata or {},
            "messages": [],
            "status": "active",
            "created_at": now,
        }
        await self._cache.set(self._key(session_id), session, ttl_seconds=DEFAULT_TTL)
        logger.info("session.created", session_id=session_id, user_id=user_id)
        return session

    async def get_session(self, session_id: str) -> dict[str, Any]:
        """Retrieve a session by its identifier."""
        session = await self._cache.get(self._key(session_id))
        if session is None:
            raise KeyError(f"Session {session_id} not found or expired")
        return session

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        """Append a message to an active session."""
        session = await self.get_session(session_id)
        session["messages"].append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        await self._cache.set(self._key(session_id), session, ttl_seconds=DEFAULT_TTL)

    async def close_session(
        self,
        session_id: str,
        extract_memories: bool = True,
    ) -> dict[str, Any]:
        """Close a session and optionally extract long-term memories."""
        session = await self.get_session(session_id)
        session["status"] = "closed"

        extracted: list[dict[str, Any]] = []
        if extract_memories and session.get("messages"):
            extracted = await self._memory_extractor.extract(session)

        await self._cache.delete(self._key(session_id))
        logger.info("session.closed", session_id=session_id, memories=len(extracted))

        return {
            "status": "closed",
            "extracted_memories": extracted,
            "session": session,
        }
