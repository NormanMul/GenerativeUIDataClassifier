"""UDC VisionLens — Screen parser tests."""

import pytest

from udc_visionlens.core.screen_parser import ScreenParser


class TestScreenParser:
    """Tests for the ScreenParser pipeline."""

    def test_placeholder(self) -> None:
        """Verify ScreenParser can be instantiated."""
        parser = ScreenParser()
        assert parser is not None
