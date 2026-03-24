"""UDC DesktopAgent — Tests for the task planner."""

import pytest

from udc_desktopagent.core.task_planner import TaskPlanner


class TestTaskPlanner:
    """Tests for TaskPlanner decomposition."""

    def test_placeholder(self) -> None:
        """Verify TaskPlanner can be instantiated."""
        planner = TaskPlanner()
        assert planner is not None

    @pytest.mark.asyncio
    async def test_plan_raises_not_implemented(self) -> None:
        """Verify plan raises NotImplementedError until implemented."""
        planner = TaskPlanner()
        with pytest.raises(NotImplementedError):
            await planner.plan("open spreadsheet", b"fake_screenshot")
