"""UDC DesktopAgent — Task execution endpoint for multi-step desktop workflows."""

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["tasks"])


class TaskRequest(BaseModel):
    """Request model for desktop task execution.

    Attributes:
        instruction: Natural language instruction describing the workflow.
        max_steps: Maximum number of steps the agent may execute.
        timeout_seconds: Timeout for the entire task execution.
    """

    instruction: str = Field(..., description="Natural language instruction describing the workflow")
    max_steps: int = Field(default=20, ge=1, le=100, description="Maximum steps to execute")
    timeout_seconds: int = Field(default=300, ge=1, le=3600, description="Task timeout in seconds")


@router.post("/task")
async def execute_task(request: TaskRequest) -> dict:
    """Execute a multi-step desktop workflow from a natural language instruction.

    Args:
        request: Task execution parameters including instruction and constraints.

    Returns:
        Task execution result with status and step details.

    Raises:
        NotImplementedError: Agent loop not yet implemented.
    """
    logger.info(
        "task_received",
        instruction=request.instruction,
        max_steps=request.max_steps,
        timeout_seconds=request.timeout_seconds,
    )
    raise NotImplementedError("Task execution not yet implemented")
