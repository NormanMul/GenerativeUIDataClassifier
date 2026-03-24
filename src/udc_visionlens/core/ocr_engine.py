"""UDC VisionLens — OCR text extraction engine.

Provides text extraction from UI element regions with dual-backend support:
- **Primary**: Azure AI Vision for cloud-grade accuracy.
- **Fallback**: Tesseract OCR for offline / local operation.
"""

import structlog
from PIL import Image

from udc_visionlens.models.ui_element import BoundingBox

logger = structlog.get_logger(__name__)


class OCREngine:
    """Extract text from image regions using Azure AI Vision or Tesseract.

    Primary backend is Azure AI Vision. Falls back to Tesseract when the
    Azure endpoint is unavailable or not configured.
    """

    def extract_text(self, image: Image.Image, bbox: BoundingBox) -> str:
        """Extract text from a specific region of an image.

        Args:
            image: Full screenshot as a PIL Image.
            bbox: Bounding box defining the region to extract text from.

        Returns:
            Extracted text string from the specified region.

        Raises:
            NotImplementedError: OCR extraction not yet implemented.
        """
        logger.info("ocr_extract_start", bbox=bbox.model_dump())
        raise NotImplementedError("OCREngine.extract_text is not yet implemented")
