"""UDC MetaCatalog — Redis Pub/Sub event handlers.

Subscribes to asset and quality events and triggers catalog-side reactions
such as auto-tagging from the business glossary and quality score updates.
"""

import asyncio
import json
from typing import Any

import structlog
from redis.asyncio import Redis

logger = structlog.get_logger(__name__)


async def start_event_listeners(redis: Redis) -> asyncio.Task:
    """Start background task that listens to MetaCatalog-relevant channels."""
    task = asyncio.create_task(_listen(redis))
    logger.info("metacatalog.events.listeners_started")
    return task


async def _listen(redis: Redis) -> None:
    """Subscribe to relevant channels and dispatch to handlers."""
    pubsub = redis.pubsub()
    await pubsub.subscribe(
        "udc:asset:registered",
        "udc:quality:reported",
    )
    logger.info("metacatalog.events.subscribed", channels=["udc:asset:registered", "udc:quality:reported"])

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue

            channel = message["channel"]
            if isinstance(channel, bytes):
                channel = channel.decode()

            try:
                data = json.loads(message["data"])
            except (json.JSONDecodeError, TypeError):
                logger.warning("metacatalog.events.invalid_message", channel=channel)
                continue

            if channel == "udc:asset:registered":
                await _on_asset_registered(data)
            elif channel == "udc:quality:reported":
                await _on_quality_reported(data, redis)
    except asyncio.CancelledError:
        logger.info("metacatalog.events.listener_cancelled")
    finally:
        await pubsub.unsubscribe()
        await pubsub.close()


async def _on_asset_registered(data: dict[str, Any]) -> None:
    """Handle a new asset registration event.

    - Log the event
    - Trigger auto-tagging from the business glossary if glossary terms exist
    """
    asset_id = data.get("asset_id", "unknown")
    asset_name = data.get("name", "")
    logger.info("metacatalog.events.asset_registered", asset_id=asset_id, name=asset_name)

    # Auto-tag from glossary if terms are available
    try:
        from glossary.auto_tagger import auto_tag_asset

        tags_added = await auto_tag_asset(asset_id)
        if tags_added:
            logger.info(
                "metacatalog.events.auto_tagged",
                asset_id=asset_id,
                tags_added=tags_added,
            )
    except ImportError:
        logger.debug("metacatalog.events.auto_tagger_not_available")
    except Exception as e:
        logger.error("metacatalog.events.auto_tag_error", asset_id=asset_id, error=str(e))


async def _on_quality_reported(data: dict[str, Any], redis: Redis) -> None:
    """Handle a quality report event.

    - Update the asset's quality_score field in the database
    """
    asset_id = data.get("asset_id", "unknown")
    overall_score = data.get("overall_score")
    logger.info("metacatalog.events.quality_reported", asset_id=asset_id, score=overall_score)

    if overall_score is None:
        return

    try:
        from core.database import get_session
        from core.models import Asset
        from sqlalchemy import update

        async for session in get_session():
            await session.execute(
                update(Asset)
                .where(Asset.id == asset_id)
                .values(quality_score=float(overall_score))
            )
            await session.commit()
            logger.info("metacatalog.events.quality_score_updated", asset_id=asset_id, score=overall_score)
    except Exception as e:
        logger.error("metacatalog.events.quality_update_error", asset_id=asset_id, error=str(e))
