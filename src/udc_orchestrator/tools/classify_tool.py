"""UDC Orchestrator — Copilot tool definition for data classification.

Provides the classify_data tool that calls the UDC Classifier subsystem
via gRPC/REST to classify data assets by PII, sensitivity, and domain.
"""

from dataclasses import dataclass
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

TOOL_NAME = "classify_data"
TOOL_DESCRIPTION = (
    "Classify data assets using the UDC Classifier engine. "
    "Detects PII, sensitivity levels, and domain tags for columns."
)
TOOL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "asset_id": {
            "type": "string",
            "description": "Unique identifier of the data asset to classify",
        },
        "column_name": {
            "type": "string",
            "description": "Specific column to classify (optional, classifies all if omitted)",
        },
    },
    "required": ["asset_id"],
}


@dataclass
class ClassificationResult:
    """Result of a data classification operation."""

    asset_id: str
    column_name: str | None
    pii_detected: bool
    sensitivity_level: str
    domain_tags: list[str]
    confidence: float
    details: dict[str, Any]


async def classify_data(
    asset_id: str, column_name: str | None = None
) -> dict[str, Any]:
    """Classify a data asset or specific column via the UDC Classifier.

    Calls the Classifier subsystem through gRPC (preferred) or REST fallback
    to perform multi-label classification including PII detection, sensitivity
    scoring, and domain tagging.

    Args:
        asset_id: The unique identifier of the data asset.
        column_name: Optional column name for targeted classification.

    Returns:
        Classification result as a dictionary.
    """
    logger.info(
        "tool.classify_data",
        asset_id=asset_id,
        column_name=column_name,
    )
    raise NotImplementedError(
        "classify_data tool — Classifier gRPC/REST integration not yet implemented"
    )
