"""UDC MetaCatalog — Data quality validators."""

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class ReferentialIntegrityValidator:
    """Validate that foreign key references exist in target tables."""

    async def validate(self, source_col: Any, target_table: str, target_col: str) -> dict[str, Any]:
        """Check referential integrity between source and target columns."""
        raise NotImplementedError("Referential integrity validation not yet implemented")


class UniquenessValidator:
    """Validate uniqueness constraints on column combinations."""

    async def validate(self, table_data: Any, columns: list[str]) -> dict[str, Any]:
        """Check that values in specified columns are unique."""
        raise NotImplementedError("Uniqueness validation not yet implemented")


class TypeConsistencyValidator:
    """Validate that column values match expected data types."""

    async def validate(self, column_data: Any, expected_type: str) -> dict[str, Any]:
        """Check type consistency."""
        raise NotImplementedError("Type consistency validation not yet implemented")
