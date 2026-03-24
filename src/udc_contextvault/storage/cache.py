"""UDC ContextVault — Redis caching layer for hot context entries.

Provides a TTL-aware cache in front of the document and vector stores
to reduce latency for frequently accessed context paths.
"""

from __future__ import annotations

import json
import os
from typing import Any

import redis.asyncio as aioredis
import structlog

logger = structlog.get_logger(__name__)


class RedisContextCache:
    """Cache frequently accessed context entries in Redis.

    Supports simple get / set / invalidate with configurable TTL
    per entry.
    """

    def __init__(self) -> None:
        url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self._redis = aioredis.from_url(url, decode_responses=True)

    async def get(self, key: str) -> Any | None:
        """Retrieve a cached value with JSON deserialization."""
        raw = await self._redis.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Store a value in the cache with a TTL and JSON serialization."""
        serialized = json.dumps(value) if not isinstance(value, str) else value
        await self._redis.set(key, serialized, ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        """Remove a key from the cache."""
        await self._redis.delete(key)

    async def invalidate(self, key: str) -> None:
        """Remove a key from the cache (alias for delete)."""
        await self.delete(key)

    async def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching a glob pattern.

        Uses SCAN to avoid blocking the server on large keyspaces.

        Returns:
            Number of keys deleted.
        """
        deleted = 0
        async for key in self._redis.scan_iter(match=pattern, count=200):
            await self._redis.delete(key)
            deleted += 1
        if deleted:
            logger.info("cache.invalidate_pattern", pattern=pattern, deleted=deleted)
        return deleted

    async def close(self) -> None:
        await self._redis.aclose()
