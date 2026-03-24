"""UDC DesktopAgent — LLM-powered task planner for action decomposition."""

import structlog

logger = structlog.get_logger(__name__)


class TaskPlanner:
    """Decomposes high-level instructions into subtask sequences via LLM.

    Takes a natural language instruction and the current screen state,
    then produces an ordered list of concrete actions for the agent to
    execute.
    """

    async def plan(self, instruction: str, screen_state: bytes) -> list[dict]:
        """Decompose a high-level task into a sequence of subtasks.

        Sends the instruction and current screen state to the LLM to
        produce a structured plan of actions.

        Args:
            instruction: Natural language description of the task.
            screen_state: Current screenshot as PNG bytes.

        Returns:
            Ordered list of action dictionaries, each containing at minimum
            an ``action_type`` key and relevant parameters.

        Raises:
            NotImplementedError: Task planner not yet implemented.
        """
        logger.info("task_planner_plan", instruction=instruction)
        raise NotImplementedError("Task planner not yet implemented")
