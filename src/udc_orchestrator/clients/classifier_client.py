"""Async gRPC client for UDC Classifier service (.NET)."""

from __future__ import annotations

import os
from typing import Any

import grpc
import structlog
from grpc import aio

from shared_grpc import classifier_pb2, classifier_pb2_grpc

logger = structlog.get_logger(__name__)


class ClassifierClient:
    """Async gRPC client wrapping the ClassifierService."""

    def __init__(self, channel: aio.Channel) -> None:
        self._channel = channel
        self._stub = classifier_pb2_grpc.ClassifierServiceStub(channel)

    @classmethod
    def connect(cls, host: str | None = None, port: int | None = None) -> ClassifierClient:
        """Create a client connected to the Classifier gRPC server."""
        host = host or os.environ.get("CLASSIFIER_GRPC_HOST", "localhost")
        port = port or int(os.environ.get("CLASSIFIER_GRPC_PORT", "50051"))
        channel = aio.insecure_channel(f"{host}:{port}")
        logger.info("classifier_client.connected", host=host, port=port)
        return cls(channel)

    async def close(self) -> None:
        """Close the underlying gRPC channel."""
        await self._channel.close()

    async def classify(
        self,
        asset_id: str,
        column_name: str,
        sample_values: list[str],
        statistics: dict[str, Any] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Classify a single column."""
        try:
            stats = None
            if statistics:
                stats = classifier_pb2.ColumnStatistics(**statistics)

            request = classifier_pb2.ClassifyRequest(
                asset_id=asset_id,
                column_name=column_name,
                sample_values=sample_values,
                statistics=stats,
                metadata=metadata or {},
            )
            response = await self._stub.Classify(request)
            return {
                "result": _proto_to_dict(response.result) if response.result else None,
                "request_id": response.request_id,
            }
        except grpc.RpcError as e:
            logger.error("classifier_client.classify.error", code=e.code(), details=e.details())
            raise

    async def classify_batch(
        self, requests: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Classify a batch of columns."""
        try:
            pb_requests = [
                classifier_pb2.ClassifyRequest(
                    asset_id=r["asset_id"],
                    column_name=r["column_name"],
                    sample_values=r.get("sample_values", []),
                    metadata=r.get("metadata", {}),
                )
                for r in requests
            ]
            request = classifier_pb2.ClassifyBatchRequest(requests=pb_requests)
            response = await self._stub.ClassifyBatch(request)
            return {
                "results": [_proto_to_dict(r) for r in response.results],
                "batch_id": response.batch_id,
                "total_processed": response.total_processed,
                "total_errors": response.total_errors,
            }
        except grpc.RpcError as e:
            logger.error("classifier_client.classify_batch.error", code=e.code(), details=e.details())
            raise


def _proto_to_dict(msg: Any) -> dict[str, Any]:
    """Convert a protobuf message to a plain dict."""
    from google.protobuf.json_format import MessageToDict

    return MessageToDict(msg, preserving_proto_field_name=True)
