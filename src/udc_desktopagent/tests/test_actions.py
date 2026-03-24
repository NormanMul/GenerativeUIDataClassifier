"""UDC DesktopAgent — Tests for the action executor."""

import pytest

from udc_desktopagent.core.action_executor import ActionExecutor


class TestActionExecutor:
    """Tests for ActionExecutor operations."""

    def test_placeholder(self) -> None:
        """Verify ActionExecutor can be instantiated."""
        executor = ActionExecutor()
        assert executor is not None

    @pytest.mark.asyncio
    async def test_click_raises_not_implemented(self) -> None:
        """Verify click raises NotImplementedError until implemented."""
        executor = ActionExecutor()
        with pytest.raises(NotImplementedError):
            await executor.click(100, 200)
