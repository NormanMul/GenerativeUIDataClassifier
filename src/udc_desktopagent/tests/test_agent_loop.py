"""UDC DesktopAgent — Tests for the agent loop."""

import pytest

from udc_desktopagent.core.agent_loop import AgentLoop, TaskResult


class TestAgentLoop:
    """Tests for AgentLoop orchestration."""

    def test_placeholder(self) -> None:
        """Verify AgentLoop can be instantiated."""
        loop = AgentLoop()
        assert loop is not None

    @pytest.mark.asyncio
    async def test_execute_raises_not_implemented(self) -> None:
        """Verify execute raises NotImplementedError until implemented."""
        loop = AgentLoop()
        with pytest.raises(NotImplementedError):
            await loop.execute("open calculator")
