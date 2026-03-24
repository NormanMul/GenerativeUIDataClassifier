"""UDC VisionLens — Screen state data model."""

from datetime import datetime

from pydantic import BaseModel, Field

from udc_visionlens.models.ui_element import UIElement


class ScreenState(BaseModel):
    """Snapshot of a parsed screen with all detected UI elements."""

    elements: list[UIElement] = Field(default_factory=list, description="Detected UI elements")
    screenshot_b64: str = Field(..., description="Base64-encoded screenshot image")
    screen_width: int = Field(..., ge=1, description="Screenshot width in pixels")
    screen_height: int = Field(..., ge=1, description="Screenshot height in pixels")
    captured_at: datetime = Field(default_factory=datetime.utcnow, description="Capture timestamp (UTC)")
