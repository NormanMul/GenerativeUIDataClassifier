"""UDC Orchestrator — Workflow execution endpoints."""

from typing import Any

import structlog
from fastapi import APIRouter
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

router = APIRouter()


class WorkflowRequest(BaseModel):
    """Request to execute a named workflow."""

    workflow_name: str
    parameters: dict[str, Any] = {}


class WorkflowResponse(BaseModel):
    """Response from workflow execution."""

    workflow_id: str
    status: str
    result: dict[str, Any] | None = None


class WorkflowStatus(BaseModel):
    """Workflow execution status."""

    workflow_id: str
    status: str
    current_step: str | None = None
    progress: float = 0.0
    error: str | None = None


@router.post("/workflow", response_model=WorkflowResponse)
async def execute_workflow(request: WorkflowRequest) -> WorkflowResponse:
    """Execute a named workflow with the given parameters.

    Loads the workflow DAG definition, resolves dependencies,
    and executes steps with retry and checkpoint support.
    """
    logger.info(
        "workflow.execute.requested",
        workflow_name=request.workflow_name,
        parameters=request.parameters,
    )
    raise NotImplementedError("Workflow execution not yet implemented")


@router.get("/workflow/{workflow_id}/status", response_model=WorkflowStatus)
async def get_workflow_status(workflow_id: str) -> WorkflowStatus:
    """Get the current status of a running or completed workflow."""
    logger.info("workflow.status.requested", workflow_id=workflow_id)
    raise NotImplementedError("Workflow status retrieval not yet implemented")
