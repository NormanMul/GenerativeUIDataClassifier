"""UDC MetaCatalog — Redis Pub/Sub event bus for async events."""

import json
import os
from typing import Any, Callable

import structlog
from redis.asyncio import Redis

logger = structlog.get_logger(__name__)

_redis: Redis | None = None
_subscribers: dict[str, list[Callable]] = {}


async def init_event_bus() -> None:
    """Initialize Redis connection for event bus."""
    global _redis
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    _redis = Redis.from_url(redis_url, decode_responses=True)
    logger.info("event_bus.initialized", redis_url=redis_url)


async def close_event_bus() -> None:
    """Close Redis connection."""
    global _redis
    if _redis:
        await _redis.close()
        logger.info("event_bus.closed")


async def publish_event(event_type: str, payload: dict[str, Any]) -> None:
    """Publish an event to Redis Pub/Sub."""
    if _redis is None:
        logger.warning("event_bus.not_initialized", event_type=event_type)
        return

    message = json.dumps({"event_type": event_type, "payload": payload})
    await _redis.publish(f"udc:events:{event_type}", message)
    logger.info("event_bus.published", event_type=event_type)
