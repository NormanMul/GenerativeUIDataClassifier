"""UDC Orchestrator — Interactive chat endpoint with SSE streaming."""

from typing import Any

import structlog
from fastapi import APIRouter
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

router = APIRouter()


class ChatMessage(BaseModel):
    """A single chat message."""

    role: str
    content: str


class ChatRequest(BaseModel):
    """Request for interactive NL chat interface."""

    messages: list[ChatMessage]
    context: dict[str, Any] = {}
    stream: bool = True


@router.post("/chat")
async def chat(request: ChatRequest) -> Any:
    """Interactive natural-language interface to UDC subsystems.

    Accepts user messages, routes through CopilotBridge with registered tools,
    and returns a streaming SSE response for real-time feedback.
    """
    logger.info(
        "chat.requested",
        message_count=len(request.messages),
        stream=request.stream,
    )
    raise NotImplementedError("Chat endpoint not yet implemented — requires CopilotBridge")
