"""Async gRPC client for UDC MetaCatalog service."""

from __future__ import annotations

import os
from typing import Any

import grpc
import structlog
from grpc import aio

from shared_grpc import metadata_pb2, metadata_pb2_grpc

logger = structlog.get_logger(__name__)


class MetaCatalogClient:
    """Async gRPC client wrapping the MetadataService."""

    def __init__(self, channel: aio.Channel) -> None:
        self._channel = channel
        self._stub = metadata_pb2_grpc.MetadataServiceStub(channel)

    @classmethod
    def connect(cls, host: str | None = None, port: int | None = None) -> MetaCatalogClient:
        """Create a client connected to the MetaCatalog gRPC server."""
        host = host or os.environ.get("METACATALOG_GRPC_HOST", "localhost")
        port = port or int(os.environ.get("METACATALOG_GRPC_PORT", "50052"))
        channel = aio.insecure_channel(f"{host}:{port}")
        logger.info("metacatalog_client.connected", host=host, port=port)
        return cls(channel)

    async def close(self) -> None:
        """Close the underlying gRPC channel."""
        await self._channel.close()

    async def register_asset(self, asset: dict[str, Any]) -> dict[str, Any]:
        """Register a new data asset."""
        try:
            pb_asset = metadata_pb2.DataAsset(**asset)
            request = metadata_pb2.RegisterAssetRequest(asset=pb_asset)
            response = await self._stub.RegisterAsset(request)
            return {"asset_id": response.asset_id, "created": response.created}
        except grpc.RpcError as e:
            logger.error("metacatalog_client.register_asset.error", code=e.code(), details=e.details())
            raise

    async def get_asset(self, asset_id: str) -> dict[str, Any]:
        """Retrieve a data asset by ID."""
        try:
            request = metadata_pb2.GetAssetRequest(asset_id=asset_id)
            response = await self._stub.GetAsset(request)
            return _proto_to_dict(response)
        except grpc.RpcError as e:
            logger.error("metacatalog_client.get_asset.error", code=e.code(), details=e.details())
            raise

    async def get_lineage(
        self,
        asset_id: str,
        direction: str = "both",
        depth: int = 3,
        column_name: str | None = None,
    ) -> dict[str, Any]:
        """Retrieve lineage graph for an asset."""
        try:
            request = metadata_pb2.GetLineageRequest(
                asset_id=asset_id,
                direction=direction,
                depth=depth,
                column_name=column_name or "",
            )
            response = await self._stub.GetLineage(request)
            return {
                "nodes": [_proto_to_dict(n) for n in response.nodes],
                "edges": [_proto_to_dict(e) for e in response.edges],
            }
        except grpc.RpcError as e:
            logger.error("metacatalog_client.get_lineage.error", code=e.code(), details=e.details())
            raise

    async def get_quality_report(self, asset_id: str) -> dict[str, Any]:
        """Retrieve the quality report for an asset."""
        try:
            request = metadata_pb2.GetQualityReportRequest(asset_id=asset_id)
            response = await self._stub.GetQualityReport(request)
            return _proto_to_dict(response)
        except grpc.RpcError as e:
            logger.error("metacatalog_client.get_quality_report.error", code=e.code(), details=e.details())
            raise


def _proto_to_dict(msg: Any) -> dict[str, Any]:
    """Convert a protobuf message to a plain dict via MessageToDict semantics."""
    from google.protobuf.json_format import MessageToDict

    return MessageToDict(msg, preserving_proto_field_name=True)
