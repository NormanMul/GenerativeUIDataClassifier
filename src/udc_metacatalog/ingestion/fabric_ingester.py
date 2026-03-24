"""UDC MetaCatalog — Microsoft Fabric Lakehouse metadata ingester."""

from typing import Any

import structlog

from ingestion.base import BaseIngester

logger = structlog.get_logger(__name__)


class FabricIngester(BaseIngester):
    """Scan Microsoft Fabric Lakehouse via REST API and register assets."""

    def __init__(self, workspace_id: str, lakehouse_id: str) -> None:
        """Initialize Fabric Lakehouse ingester.

        Args:
            workspace_id: Fabric workspace ID.
            lakehouse_id: Lakehouse identifier.
        """
        super().__init__(source_type="fabric", source_instance=f"{workspace_id}/{lakehouse_id}")
        self.workspace_id = workspace_id
        self.lakehouse_id = lakehouse_id

    async def scan(self) -> list[dict[str, Any]]:
        """Scan Fabric Lakehouse tables via REST API."""
        raise NotImplementedError("Fabric Lakehouse scanning not yet implemented")

    async def register_assets(self, raw_metadata: list[dict[str, Any]]) -> int:
        """Register discovered Fabric assets in the catalog."""
        raise NotImplementedError("Fabric asset registration not yet implemented")
