"""UDC VisionLens — Screen parsing endpoint."""

import structlog
from fastapi import APIRouter, UploadFile

from udc_visionlens.models.screen_state import ScreenState

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/parse", response_model=ScreenState)
async def parse_screenshot(screenshot: UploadFile) -> ScreenState:
    """Parse a screenshot and return structured UI elements.

    Args:
        screenshot: Uploaded screenshot image file.

    Returns:
        Structured screen state with detected UI elements.

    Raises:
        NotImplementedError: Pipeline not yet implemented.
    """
    logger.info("parse_request", filename=screenshot.filename, content_type=screenshot.content_type)
    raise NotImplementedError("Screen parsing pipeline is not yet implemented")
