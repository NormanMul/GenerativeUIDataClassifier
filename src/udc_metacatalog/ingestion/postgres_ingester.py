"""UDC MetaCatalog — PostgreSQL WMS metadata ingester."""

from typing import Any

import structlog

from ingestion.base import BaseIngester

logger = structlog.get_logger(__name__)


class PostgresIngester(BaseIngester):
    """Scan PostgreSQL WMS instances and register tables/columns as data assets.

    Connects to information_schema to discover tables, columns, constraints,
    and basic statistics for each of the 57-100 store databases.
    """

    def __init__(self, connection_string: str, source_instance: str) -> None:
        """Initialize PostgreSQL ingester.

        Args:
            connection_string: PostgreSQL connection string.
            source_instance: Store identifier (e.g., 'store_01').
        """
        super().__init__(source_type="postgres", source_instance=source_instance)
        self.connection_string = connection_string

    async def scan(self) -> list[dict[str, Any]]:
        """Scan PostgreSQL information_schema for tables and columns."""
        raise NotImplementedError("PostgreSQL scanning not yet implemented")

    async def register_assets(self, raw_metadata: list[dict[str, Any]]) -> int:
        """Register discovered PostgreSQL assets in the catalog."""
        raise NotImplementedError("PostgreSQL asset registration not yet implemented")
