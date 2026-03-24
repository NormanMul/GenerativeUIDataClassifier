"""UDC MetaCatalog — Abstract base ingestion connector."""

from abc import ABC, abstractmethod
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class BaseIngester(ABC):
    """Abstract base class for metadata ingestion connectors.

    All ingesters must implement scan() and register_assets() methods.
    """

    def __init__(self, source_type: str, source_instance: str) -> None:
        """Initialize the ingester.

        Args:
            source_type: Type of data source (postgres, sap, fabric).
            source_instance: Instance identifier (e.g., store ID, connection name).
        """
        self.source_type = source_type
        self.source_instance = source_instance

    @abstractmethod
    async def scan(self) -> list[dict[str, Any]]:
        """Scan the data source and return raw metadata.

        Returns:
            List of raw asset metadata dictionaries.
        """
        ...

    @abstractmethod
    async def register_assets(self, raw_metadata: list[dict[str, Any]]) -> int:
        """Register discovered assets in the MetaCatalog.

        Args:
            raw_metadata: Raw metadata from scan().

        Returns:
            Number of assets registered or updated.
        """
        ...

    async def refresh(self) -> int:
        """Full refresh: scan → register.

        Returns:
            Number of assets registered or updated.
        """
        logger.info("ingestion.refresh.start", source_type=self.source_type, instance=self.source_instance)
        raw = await self.scan()
        count = await self.register_assets(raw)
        logger.info("ingestion.refresh.complete", source_type=self.source_type, instance=self.source_instance, count=count)
        return count
