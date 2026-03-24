"""UDC VisionLens — Element detector tests."""

import pytest

from udc_visionlens.core.element_detector import ElementDetector


class TestElementDetector:
    """Tests for the ElementDetector."""

    def test_placeholder(self) -> None:
        """Verify ElementDetector can be instantiated."""
        detector = ElementDetector()
        assert detector is not None
