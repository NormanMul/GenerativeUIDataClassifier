"""Async gRPC client for UDC ContextVault service."""

from __future__ import annotations

import os
from typing import Any

import grpc
import structlog
from grpc import aio

from shared_grpc import context_pb2, context_pb2_grpc

logger = structlog.get_logger(__name__)


class ContextVaultClient:
    """Async gRPC client wrapping the ContextVaultService."""

    def __init__(self, channel: aio.Channel) -> None:
        self._channel = channel
        self._stub = context_pb2_grpc.ContextVaultServiceStub(channel)

    @classmethod
    def connect(cls, host: str | None = None, port: int | None = None) -> ContextVaultClient:
        """Create a client connected to the ContextVault gRPC server."""
        host = host or os.environ.get("CONTEXTVAULT_GRPC_HOST", "localhost")
        port = port or int(os.environ.get("CONTEXTVAULT_GRPC_PORT", "50053"))
        channel = aio.insecure_channel(f"{host}:{port}")
        logger.info("contextvault_client.connected", host=host, port=port)
        return cls(channel)

    async def close(self) -> None:
        """Close the underlying gRPC channel."""
        await self._channel.close()

    async def store_context(
        self,
        path: str,
        content: str,
        metadata: dict[str, str] | None = None,
        session_id: str | None = None,
    ) -> dict[str, str]:
        """Store a context entry in the vault."""
        try:
            request = context_pb2.AddContextRequest(
                path=path,
                content=content,
                metadata=metadata or {},
                session_id=session_id or "",
            )
            response = await self._stub.AddContext(request)
            return {"context_id": response.context_id, "path": response.path}
        except grpc.RpcError as e:
            logger.error("contextvault_client.store_context.error", code=e.code(), details=e.details())
            raise

    async def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        namespace: str = "",
        layer: int = 2,
        filters: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve context entries by semantic similarity."""
        try:
            request = context_pb2.FindContextRequest(
                query=query,
                top_k=top_k,
                namespace=namespace,
                layer=layer,
                filters=filters or {},
            )
            response = await self._stub.FindContext(request)
            return [
                {"entry": _proto_to_dict(r.entry), "score": r.score}
                for r in response.results
            ]
        except grpc.RpcError as e:
            logger.error("contextvault_client.retrieve_context.error", code=e.code(), details=e.details())
            raise

    async def get_session_context(self, session_id: str) -> dict[str, Any]:
        """Retrieve a session and its context."""
        try:
            request = context_pb2.GetSessionRequest(session_id=session_id)
            response = await self._stub.GetSession(request)
            return _proto_to_dict(response)
        except grpc.RpcError as e:
            logger.error("contextvault_client.get_session_context.error", code=e.code(), details=e.details())
            raise


def _proto_to_dict(msg: Any) -> dict[str, Any]:
    """Convert a protobuf message to a plain dict."""
    from google.protobuf.json_format import MessageToDict

    return MessageToDict(msg, preserving_proto_field_name=True)
