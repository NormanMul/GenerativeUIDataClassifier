"""UDC VisionLens — UI element detection using YOLO."""

import os

import structlog
from PIL import Image

from udc_visionlens.models.ui_element import UIElement

logger = structlog.get_logger(__name__)


class ElementDetector:
    """Detect UI elements in screenshots using a YOLO object-detection model.

    The model path is loaded from the ``VISIONLENS_MODEL_PATH`` environment
    variable at initialisation time.
    """

    def __init__(self) -> None:
        """Initialise the detector and resolve the model path."""
        self.model_path: str = os.getenv("VISIONLENS_MODEL_PATH", "models/yolo_ui.pt")
        logger.info("element_detector_init", model_path=self.model_path)

    def detect(self, image: Image.Image) -> list[UIElement]:
        """Run element detection on a screenshot image.

        Args:
            image: PIL Image of the screenshot to analyse.

        Returns:
            List of detected UI elements with bounding boxes and metadata.

        Raises:
            NotImplementedError: YOLO detection not yet implemented.
        """
        logger.info("element_detect_start", image_size=image.size)
        raise NotImplementedError("ElementDetector.detect is not yet implemented")
