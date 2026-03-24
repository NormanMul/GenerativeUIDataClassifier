"""UDC Orchestrator — Tests for CopilotBridge."""

import pytest

from udc_orchestrator.core.copilot_bridge import CopilotBridge


class TestCopilotBridge:
    """Test suite for the CopilotBridge class."""

    def test_placeholder(self) -> None:
        """Placeholder test — validates CopilotBridge can be instantiated."""
        bridge = CopilotBridge()
        assert bridge is not None
        assert bridge._initialized is False

    @pytest.mark.asyncio
    async def test_initialize_not_implemented(self) -> None:
        """Verify initialize raises NotImplementedError."""
        bridge = CopilotBridge()
        with pytest.raises(NotImplementedError):
            await bridge.initialize({"endpoint": "http://localhost"})

    @pytest.mark.asyncio
    async def test_chat_not_implemented(self) -> None:
        """Verify chat raises NotImplementedError."""
        bridge = CopilotBridge()
        with pytest.raises(NotImplementedError):
            await bridge.chat([{"role": "user", "content": "hello"}])
