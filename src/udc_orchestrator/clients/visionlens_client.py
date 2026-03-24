"""Async gRPC client for UDC VisionLens service."""

from __future__ import annotations

import os
from typing import Any

import grpc
import structlog
from grpc import aio

from shared_grpc import vision_pb2, vision_pb2_grpc

logger = structlog.get_logger(__name__)


class VisionLensClient:
    """Async gRPC client wrapping the VisionLensService."""

    def __init__(self, channel: aio.Channel) -> None:
        self._channel = channel
        self._stub = vision_pb2_grpc.VisionLensServiceStub(channel)

    @classmethod
    def connect(cls, host: str | None = None, port: int | None = None) -> VisionLensClient:
        """Create a client connected to the VisionLens gRPC server."""
        host = host or os.environ.get("VISIONLENS_GRPC_HOST", "localhost")
        port = port or int(os.environ.get("VISIONLENS_GRPC_PORT", "50054"))
        channel = aio.insecure_channel(f"{host}:{port}")
        logger.info("visionlens_client.connected", host=host, port=port)
        return cls(channel)

    async def close(self) -> None:
        """Close the underlying gRPC channel."""
        await self._channel.close()

    async def analyze_screen(
        self,
        screenshot: bytes,
        fmt: str = "png",
        include_ocr: bool = True,
        include_caption: bool = True,
        confidence_threshold: float = 0.5,
    ) -> dict[str, Any]:
        """Parse a screenshot and return detected UI elements."""
        try:
            request = vision_pb2.ParseRequest(
                screenshot=screenshot,
                format=fmt,
                include_ocr=include_ocr,
                include_caption=include_caption,
                confidence_threshold=confidence_threshold,
            )
            response = await self._stub.ParseScreen(request)
            return {
                "screen_state": _proto_to_dict(response.screen_state) if response.screen_state else None,
                "request_id": response.request_id,
                "processing_time_ms": response.processing_time_ms,
            }
        except grpc.RpcError as e:
            logger.error("visionlens_client.analyze_screen.error", code=e.code(), details=e.details())
            raise

    async def ground_text(
        self,
        screenshot: bytes,
        instruction: str,
    ) -> dict[str, Any]:
        """Ground a text instruction to screen coordinates."""
        try:
            request = vision_pb2.GroundTextRequest(
                screenshot=screenshot,
                instruction=instruction,
            )
            response = await self._stub.GroundText(request)
            return {
                "x": response.x,
                "y": response.y,
                "confidence": response.confidence,
                "matched_element": _proto_to_dict(response.matched_element) if response.matched_element else None,
                "reasoning": response.reasoning,
            }
        except grpc.RpcError as e:
            logger.error("visionlens_client.ground_text.error", code=e.code(), details=e.details())
            raise


def _proto_to_dict(msg: Any) -> dict[str, Any]:
    """Convert a protobuf message to a plain dict."""
    from google.protobuf.json_format import MessageToDict

    return MessageToDict(msg, preserving_proto_field_name=True)
