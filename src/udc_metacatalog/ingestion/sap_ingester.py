"""UDC MetaCatalog — SAP S/4HANA metadata ingester."""

from typing import Any

import structlog

from ingestion.base import BaseIngester

logger = structlog.get_logger(__name__)


class SAPIngester(BaseIngester):
    """Scan SAP S/4HANA data dictionary via OData API and register assets."""

    def __init__(self, base_url: str, username: str, password: str) -> None:
        """Initialize SAP OData ingester.

        Args:
            base_url: SAP OData base URL.
            username: SAP username.
            password: SAP password.
        """
        super().__init__(source_type="sap", source_instance=base_url)
        self.base_url = base_url
        self.username = username
        self.password = password

    async def scan(self) -> list[dict[str, Any]]:
        """Scan SAP data dictionary entities via OData."""
        raise NotImplementedError("SAP scanning not yet implemented")

    async def register_assets(self, raw_metadata: list[dict[str, Any]]) -> int:
        """Register discovered SAP assets in the catalog."""
        raise NotImplementedError("SAP asset registration not yet implemented")
