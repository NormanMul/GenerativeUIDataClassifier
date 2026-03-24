"""UDC VisionLens — Element detection endpoint."""

import structlog
from fastapi import APIRouter, Form, UploadFile

from udc_visionlens.models.ui_element import UIElement

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/detect", response_model=UIElement)
async def detect_element(screenshot: UploadFile, description: str = Form(...)) -> UIElement:
    """Detect a specific UI element matching a natural-language description.

    Args:
        screenshot: Uploaded screenshot image file.
        description: Natural-language description of the target element
            (e.g. "the Save button in the top-right corner").

    Returns:
        The detected UI element with bounding box and metadata.

    Raises:
        NotImplementedError: Detection pipeline not yet implemented.
    """
    logger.info("detect_request", filename=screenshot.filename, description=description)
    raise NotImplementedError("Element detection pipeline is not yet implemented")
