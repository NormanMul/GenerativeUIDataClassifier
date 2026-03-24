"""UDC DesktopAgent — Single action execution endpoint."""

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["actions"])


class ActionRequest(BaseModel):
    """Request model for a single desktop action.

    Attributes:
        action_type: Type of action to perform (click, type, scroll, drag, keypress).
        x: X coordinate for mouse actions.
        y: Y coordinate for mouse actions.
        text: Text to type for type actions.
        key_combo: Key combination string (e.g. "ctrl+c") for keypress actions.
        scroll_amount: Scroll delta for scroll actions.
        drag_to_x: Destination X coordinate for drag actions.
        drag_to_y: Destination Y coordinate for drag actions.
    """

    action_type: str = Field(..., description="Action type: click, type, scroll, drag, keypress")
    x: int | None = Field(default=None, description="X coordinate for mouse actions")
    y: int | None = Field(default=None, description="Y coordinate for mouse actions")
    text: str | None = Field(default=None, description="Text to type")
    key_combo: str | None = Field(default=None, description="Key combination (e.g. 'ctrl+c')")
    scroll_amount: int | None = Field(default=None, description="Scroll delta")
    drag_to_x: int | None = Field(default=None, description="Drag destination X coordinate")
    drag_to_y: int | None = Field(default=None, description="Drag destination Y coordinate")


@router.post("/action")
async def execute_action(request: ActionRequest) -> dict:
    """Execute a single desktop action (click, type, scroll, drag, keypress).

    Args:
        request: Action parameters including type and coordinates/text.

    Returns:
        Action execution result with status.

    Raises:
        NotImplementedError: Action executor not yet implemented.
    """
    logger.info("action_received", action_type=request.action_type)
    raise NotImplementedError("Action execution not yet implemented")
