"""UDC MetaCatalog — LLM-powered auto-tagging of columns to glossary terms."""

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class AutoTagger:
    """Map data asset columns to business glossary terms using LLM.

    Sends column names + sample values to Azure OpenAI and receives
    suggested glossary term mappings with confidence scores.
    """

    async def tag_asset_columns(self, asset_id: str) -> list[dict[str, Any]]:
        """Auto-tag all columns of an asset to glossary terms.

        Args:
            asset_id: Data asset identifier.

        Returns:
            List of column→term mappings with confidence scores.
        """
        raise NotImplementedError("Auto-tagging not yet implemented")
