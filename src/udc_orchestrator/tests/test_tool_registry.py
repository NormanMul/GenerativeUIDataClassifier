"""UDC Orchestrator — Tests for ToolRegistry."""

import pytest

from udc_orchestrator.core.tool_registry import ToolRegistry


class TestToolRegistry:
    """Test suite for the ToolRegistry class."""

    def test_placeholder(self) -> None:
        """Placeholder test — validates ToolRegistry can be instantiated."""
        registry = ToolRegistry()
        assert registry is not None
        assert registry._tools == {}

    @pytest.mark.asyncio
    async def test_register_not_implemented(self) -> None:
        """Verify register raises NotImplementedError."""
        registry = ToolRegistry()

        async def dummy_handler(**kwargs):  # type: ignore[no-untyped-def]
            return {}

        with pytest.raises(NotImplementedError):
            registry.register("test_tool", "A test tool", {}, dummy_handler)

    def test_list_all_not_implemented(self) -> None:
        """Verify list_all raises NotImplementedError."""
        registry = ToolRegistry()
        with pytest.raises(NotImplementedError):
            registry.list_all()
