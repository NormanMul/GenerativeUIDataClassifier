"""UDC VisionLens — Text-to-coordinate grounding.

Maps natural-language instructions (e.g. "Click the Save button") to
precise screen coordinates, enabling UI automation pipelines.
"""

import structlog
from PIL import Image

logger = structlog.get_logger(__name__)


class TextGrounding:
    """Ground natural-language descriptions to screen coordinates."""

    def ground(self, screenshot: Image.Image, instruction: str) -> tuple[int, int, float]:
        """Map a natural-language instruction to screen coordinates.

        Args:
            screenshot: Full screenshot as a PIL Image.
            instruction: Natural-language description of the target element
                (e.g. "Click the Save button").

        Returns:
            Tuple of (x, y, confidence) where x/y are pixel coordinates
            and confidence is a float between 0.0 and 1.0.

        Raises:
            NotImplementedError: Grounding not yet implemented.
        """
        logger.info("grounding_start", instruction=instruction, image_size=screenshot.size)
        raise NotImplementedError("TextGrounding.ground is not yet implemented")
