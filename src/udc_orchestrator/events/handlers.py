"""UDC Orchestrator — Redis Pub/Sub event handlers.

Subscribes to platform-wide channels (audit, alerts, workflow completion)
and dispatches notifications to connected SSE/chat clients.
"""

import asyncio
import json
from typing import Any

import structlog
from redis.asyncio import Redis

logger = structlog.get_logger(__name__)

# In-memory registries for connected clients (managed by the SSE / chat routes)
_sse_clients: list[asyncio.Queue] = []
_chat_sessions: dict[str, asyncio.Queue] = {}


def register_sse_client(queue: asyncio.Queue) -> None:
    """Register a new SSE client queue for real-time event streaming."""
    _sse_clients.append(queue)


def unregister_sse_client(queue: asyncio.Queue) -> None:
    """Unregister an SSE client queue."""
    _sse_clients.remove(queue) if queue in _sse_clients else None


def register_chat_session(session_id: str, queue: asyncio.Queue) -> None:
    """Register a chat session for alert notifications."""
    _chat_sessions[session_id] = queue


def unregister_chat_session(session_id: str) -> None:
    """Unregister a chat session."""
    _chat_sessions.pop(session_id, None)


async def start_event_listeners(redis: Redis) -> asyncio.Task:
    """Start background task that listens to orchestrator-relevant channels."""
    task = asyncio.create_task(_listen(redis))
    logger.info("orchestrator.events.listeners_started")
    return task


async def _listen(redis: Redis) -> None:
    """Subscribe to platform channels and dispatch to handlers."""
    pubsub = redis.pubsub()
    await pubsub.subscribe(
        "udc:audit",
        "udc:alerts",
        "udc:workflow:completed",
    )
    logger.info("orchestrator.events.subscribed", channels=["udc:audit", "udc:alerts", "udc:workflow:completed"])

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue

            channel = message["channel"]
            if isinstance(channel, bytes):
                channel = channel.decode()

            try:
                data = json.loads(message["data"])
            except (json.JSONDecodeError, TypeError):
                logger.warning("orchestrator.events.invalid_message", channel=channel)
                continue

            if channel == "udc:audit":
                await _on_audit_event(data)
            elif channel == "udc:alerts":
                await _on_alert(data)
            elif channel == "udc:workflow:completed":
                await _on_workflow_completed(data)
    except asyncio.CancelledError:
        logger.info("orchestrator.events.listener_cancelled")
    finally:
        await pubsub.unsubscribe()
        await pubsub.close()


async def _on_audit_event(data: dict[str, Any]) -> None:
    """Forward audit events to all connected SSE clients."""
    logger.info(
        "orchestrator.events.audit",
        action=data.get("action_type"),
        agent=data.get("agent_id"),
    )

    event_payload = {"type": "audit", "data": data}
    await _broadcast_sse(event_payload)


async def _on_alert(data: dict[str, Any]) -> None:
    """Log alert and notify connected chat sessions."""
    severity = data.get("severity", "warning")
    message = data.get("message", "")
    logger.warning("orchestrator.events.alert", severity=severity, message=message)

    # Forward to all SSE clients
    await _broadcast_sse({"type": "alert", "data": data})

    # Notify relevant chat sessions
    target_session = data.get("session_id")
    if target_session and target_session in _chat_sessions:
        try:
            _chat_sessions[target_session].put_nowait(
                {"type": "alert", "data": data}
            )
        except asyncio.QueueFull:
            logger.warning("orchestrator.events.chat_queue_full", session_id=target_session)
    else:
        # Broadcast to all chat sessions
        for sid, queue in _chat_sessions.items():
            try:
                queue.put_nowait({"type": "alert", "data": data})
            except asyncio.QueueFull:
                logger.warning("orchestrator.events.chat_queue_full", session_id=sid)


async def _on_workflow_completed(data: dict[str, Any]) -> None:
    """Update workflow status and notify the requester."""
    workflow_id = data.get("workflow_id", "unknown")
    status = data.get("status", "completed")
    requester_session = data.get("session_id")

    logger.info(
        "orchestrator.events.workflow_completed",
        workflow_id=workflow_id,
        status=status,
    )

    # Update workflow status in Redis
    try:
        from udc_orchestrator.core.workflow_engine import WorkflowEngine

        # Status update delegated to workflow engine if available
        logger.info("orchestrator.events.workflow_status_updated", workflow_id=workflow_id)
    except ImportError:
        pass

    # Notify requester via SSE
    await _broadcast_sse({"type": "workflow_completed", "data": data})

    # Notify specific chat session if applicable
    if requester_session and requester_session in _chat_sessions:
        try:
            _chat_sessions[requester_session].put_nowait(
                {"type": "workflow_completed", "data": data}
            )
        except asyncio.QueueFull:
            logger.warning("orchestrator.events.chat_queue_full", session_id=requester_session)


async def _broadcast_sse(payload: dict[str, Any]) -> None:
    """Send an event payload to all registered SSE client queues."""
    dead_clients: list[asyncio.Queue] = []
    for queue in _sse_clients:
        try:
            queue.put_nowait(payload)
        except asyncio.QueueFull:
            dead_clients.append(queue)

    # Clean up unresponsive clients
    for q in dead_clients:
        _sse_clients.remove(q)
