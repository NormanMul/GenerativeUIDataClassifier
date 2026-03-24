"""UDC MetaCatalog — KPI formula registry."""

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class FormulaRegistry:
    """Store and manage KPI formulas for business metrics.

    Examples:
        - revenue = SUM(line_total)
        - margin = (revenue - cost) / revenue
        - basket_size = COUNT(items) / COUNT(DISTINCT orders)
    """

    async def register_formula(self, name: str, expression: str, description: str = "") -> dict[str, Any]:
        """Register a new KPI formula."""
        raise NotImplementedError("Formula registration not yet implemented")

    async def get_formula(self, name: str) -> dict[str, Any] | None:
        """Get a formula by name."""
        raise NotImplementedError("Formula retrieval not yet implemented")

    async def list_formulas(self) -> list[dict[str, Any]]:
        """List all registered formulas."""
        raise NotImplementedError("Formula listing not yet implemented")

    def resolve_dax(self, name: str) -> str:
        """Convert a formula to DAX expression for Power BI."""
        raise NotImplementedError("DAX resolution not yet implemented")
