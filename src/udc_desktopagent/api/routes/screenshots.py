"""UDC DesktopAgent — Screenshot capture endpoint."""

import structlog
from fastapi import APIRouter

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["screenshots"])


@router.get("/screenshot")
async def get_screenshot() -> dict:
    """Return the current screen state as a base64-encoded PNG.

    Returns:
        Dictionary with base64 PNG image data and metadata.

    Raises:
        NotImplementedError: Screenshot capture not yet implemented.
    """
    logger.info("screenshot_requested")
    raise NotImplementedError("Screenshot capture not yet implemented")
