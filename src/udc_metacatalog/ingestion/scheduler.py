"""UDC MetaCatalog — Periodic metadata refresh scheduler."""

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = structlog.get_logger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def init_scheduler() -> None:
    """Initialize the APScheduler for periodic metadata refresh."""
    global _scheduler
    _scheduler = AsyncIOScheduler()
    # TODO: Add jobs from configuration
    _scheduler.start()
    logger.info("scheduler.initialized")


async def stop_scheduler() -> None:
    """Stop the scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        logger.info("scheduler.stopped")
