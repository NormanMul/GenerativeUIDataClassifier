"""UDC VisionLens — UI element data models."""

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Axis-aligned bounding box for a UI element."""

    x: int = Field(..., description="Left edge x-coordinate in pixels")
    y: int = Field(..., description="Top edge y-coordinate in pixels")
    width: int = Field(..., ge=1, description="Box width in pixels")
    height: int = Field(..., ge=1, description="Box height in pixels")


class UIElement(BaseModel):
    """Detected UI element with spatial and semantic metadata."""

    id: str = Field(..., description="Unique element identifier")
    element_type: str = Field(..., description="Element type (button, input, label, icon, etc.)")
    bbox: BoundingBox = Field(..., description="Bounding box of the element")
    text: str = Field(default="", description="OCR-extracted text content")
    caption: str = Field(default="", description="VLM-generated functional description")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    interactable: bool = Field(default=False, description="Whether the element is interactive")
    attributes: dict[str, str] = Field(default_factory=dict, description="Additional element attributes")
