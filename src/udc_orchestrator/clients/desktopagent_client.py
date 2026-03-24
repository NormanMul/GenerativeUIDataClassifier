"""Async gRPC client for UDC DesktopAgent service."""

from __future__ import annotations

import os
from typing import Any

import grpc
import structlog
from grpc import aio

from shared_grpc import desktop_pb2, desktop_pb2_grpc

logger = structlog.get_logger(__name__)


class DesktopAgentClient:
    """Async gRPC client wrapping the DesktopAgentService."""

    def __init__(self, channel: aio.Channel) -> None:
        self._channel = channel
        self._stub = desktop_pb2_grpc.DesktopAgentServiceStub(channel)

    @classmethod
    def connect(cls, host: str | None = None, port: int | None = None) -> DesktopAgentClient:
        """Create a client connected to the DesktopAgent gRPC server."""
        host = host or os.environ.get("DESKTOPAGENT_GRPC_HOST", "localhost")
        port = port or int(os.environ.get("DESKTOPAGENT_GRPC_PORT", "50055"))
        channel = aio.insecure_channel(f"{host}:{port}")
        logger.info("desktopagent_client.connected", host=host, port=port)
        return cls(channel)

    async def close(self) -> None:
        """Close the underlying gRPC channel."""
        await self._channel.close()

    async def execute_task(
        self,
        instruction: str,
        max_steps: int = 20,
        timeout_seconds: int = 300,
        context: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Execute a desktop automation task from a natural language instruction."""
        try:
            request = desktop_pb2.TaskRequest(
                instruction=instruction,
                max_steps=max_steps,
                timeout_seconds=timeout_seconds,
                context=context or {},
            )
            response = await self._stub.ExecuteTask(request)
            return {
                "task_id": response.task_id,
                "success": response.success,
                "status": response.status,
                "steps": [_proto_to_dict(s) for s in response.steps],
                "error_message": response.error_message,
                "total_time_ms": response.total_time_ms,
            }
        except grpc.RpcError as e:
            logger.error("desktopagent_client.execute_task.error", code=e.code(), details=e.details())
            raise

    async def get_task_status(self, task_id: str) -> dict[str, Any]:
        """Get the current status of a desktop automation task."""
        try:
            request = desktop_pb2.GetTaskStatusRequest(task_id=task_id)
            response = await self._stub.GetTaskStatus(request)
            return {
                "task_id": response.task_id,
                "status": response.status,
                "current_step": response.current_step,
                "total_steps": response.total_steps,
                "current_action": response.current_action,
                "completed_steps": [_proto_to_dict(s) for s in response.completed_steps],
            }
        except grpc.RpcError as e:
            logger.error("desktopagent_client.get_task_status.error", code=e.code(), details=e.details())
            raise


def _proto_to_dict(msg: Any) -> dict[str, Any]:
    """Convert a protobuf message to a plain dict."""
    from google.protobuf.json_format import MessageToDict

    return MessageToDict(msg, preserving_proto_field_name=True)
