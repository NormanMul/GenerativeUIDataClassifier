"""UDC Orchestrator — Tests for WorkflowEngine."""

import pytest

from udc_orchestrator.core.workflow_engine import WorkflowEngine, WorkflowStatus


class TestWorkflowEngine:
    """Test suite for the WorkflowEngine class."""

    def test_placeholder(self) -> None:
        """Placeholder test — validates WorkflowEngine can be instantiated."""
        engine = WorkflowEngine()
        assert engine is not None
        assert engine._workflows == {}
        assert engine._active == {}

    @pytest.mark.asyncio
    async def test_load_workflow_not_implemented(self) -> None:
        """Verify load_workflow raises NotImplementedError."""
        engine = WorkflowEngine()
        with pytest.raises(NotImplementedError):
            await engine.load_workflow("workflows/test.yaml")

    @pytest.mark.asyncio
    async def test_execute_not_implemented(self) -> None:
        """Verify execute raises NotImplementedError."""
        engine = WorkflowEngine()
        with pytest.raises(NotImplementedError):
            await engine.execute("test_workflow", {})
