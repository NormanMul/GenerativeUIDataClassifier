"""UDC Orchestrator — Copilot tool definition for screen parsing.

Provides the parse_screen tool that calls the UDC VisionLens API
to extract structured data from screen captures and UI elements.
"""

from typing import Any

import structlog

logger = structlog.get_logger(__name__)

TOOL_NAME = "parse_screen"
TOOL_DESCRIPTION = (
    "Parse and extract structured data from screen captures using VisionLens. "
    "Identifies UI elements, tables, charts, and text regions."
)
TOOL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "image_source": {
            "type": "string",
            "description": "Path or URL to the screen capture image",
        },
        "extraction_mode": {
            "type": "string",
            "enum": ["table", "chart", "text", "ui_elements", "auto"],
            "description": "Type of data to extract from the screen",
            "default": "auto",
        },
        "region": {
            "type": "object",
            "description": "Optional bounding box region {x, y, width, height}",
        },
    },
    "required": ["image_source"],
}


async def parse_screen(
    image_source: str,
    extraction_mode: str = "auto",
    region: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Parse a screen capture and extract structured data via VisionLens.

    Args:
        image_source: Path or URL to the image.
        extraction_mode: What to extract (table, chart, text, ui_elements, auto).
        region: Optional bounding box to limit extraction area.

    Returns:
        Extracted data with element positions and confidence scores.
    """
    logger.info(
        "tool.parse_screen",
        image_source=image_source,
        extraction_mode=extraction_mode,
    )
    raise NotImplementedError(
        "parse_screen tool — VisionLens API integration not yet implemented"
    )
