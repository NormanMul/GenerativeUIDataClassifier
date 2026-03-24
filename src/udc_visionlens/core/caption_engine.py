"""UDC VisionLens — Visual caption engine for UI elements.

Uses a Vision-Language Model (VLM) to generate human-readable functional
descriptions of detected UI elements (e.g. "A blue submit button with the
label 'Save Changes'").
"""

import structlog
from PIL import Image

from udc_visionlens.models.ui_element import BoundingBox

logger = structlog.get_logger(__name__)


class CaptionEngine:
    """Generate functional descriptions of UI elements using a VLM."""

    def caption_element(self, image: Image.Image, bbox: BoundingBox) -> str:
        """Generate a natural-language caption for a UI element.

        Args:
            image: Full screenshot as a PIL Image.
            bbox: Bounding box of the element to describe.

        Returns:
            Human-readable functional description of the element.

        Raises:
            NotImplementedError: Caption generation not yet implemented.
        """
        logger.info("caption_start", bbox=bbox.model_dump())
        raise NotImplementedError("CaptionEngine.caption_element is not yet implemented")
