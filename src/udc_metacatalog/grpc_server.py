"""UDC MetaCatalog — gRPC server for metadata service."""

import asyncio
import os
from datetime import datetime, timezone

import grpc
import structlog
from grpc import aio
from sqlalchemy import select

from core.database import get_session
from core.models import Asset, LineageEdge as LineageEdgeModel, QualityCheck as QualityCheckModel

# These imports will resolve once stubs are generated via scripts/generate_grpc.sh
from shared_grpc import metadata_pb2, metadata_pb2_grpc

logger = structlog.get_logger(__name__)


class MetadataServiceServicer(metadata_pb2_grpc.MetadataServiceServicer):
    """gRPC servicer implementing the MetadataService defined in metadata.proto."""

    async def RegisterAsset(
        self,
        request: metadata_pb2.RegisterAssetRequest,
        context: grpc.aio.ServicerContext,
    ) -> metadata_pb2.RegisterAssetResponse:
        """Register a new data asset in the catalog."""
        try:
            asset_pb = request.asset
            async for session in get_session():
                # Check if asset already exists by qualified name
                existing = await session.execute(
                    select(Asset).where(Asset.qualified_name == asset_pb.qualified_name)
                )
                existing_asset = existing.scalar_one_or_none()

                if existing_asset:
                    return metadata_pb2.RegisterAssetResponse(
                        asset_id=str(existing_asset.id),
                        created=False,
                    )

                new_asset = Asset(
                    name=asset_pb.name,
                    qualified_name=asset_pb.qualified_name,
                    source_type=asset_pb.source_type,
                    source_instance=asset_pb.source_instance,
                    database_name=asset_pb.database_name,
                    schema_name=asset_pb.schema_name,
                    description=asset_pb.description,
                    tags=list(asset_pb.tags),
                    owner=asset_pb.owner,
                )
                session.add(new_asset)
                await session.commit()
                await session.refresh(new_asset)

                logger.info("grpc.asset.registered", asset_id=str(new_asset.id), name=asset_pb.name)
                return metadata_pb2.RegisterAssetResponse(
                    asset_id=str(new_asset.id),
                    created=True,
                )
        except Exception as e:
            logger.error("grpc.register_asset.error", error=str(e))
            await context.abort(grpc.StatusCode.INTERNAL, f"Failed to register asset: {e}")

    async def GetAsset(
        self,
        request: metadata_pb2.GetAssetRequest,
        context: grpc.aio.ServicerContext,
    ) -> metadata_pb2.DataAsset:
        """Retrieve a data asset by ID."""
        try:
            async for session in get_session():
                result = await session.execute(
                    select(Asset).where(Asset.id == request.asset_id)
                )
                asset = result.scalar_one_or_none()

                if asset is None:
                    await context.abort(grpc.StatusCode.NOT_FOUND, f"Asset not found: {request.asset_id}")
                    return metadata_pb2.DataAsset()

                return _asset_to_proto(asset)
        except grpc.aio.AbortError:
            raise
        except Exception as e:
            logger.error("grpc.get_asset.error", error=str(e))
            await context.abort(grpc.StatusCode.INTERNAL, f"Failed to get asset: {e}")

    async def GetLineage(
        self,
        request: metadata_pb2.GetLineageRequest,
        context: grpc.aio.ServicerContext,
    ) -> metadata_pb2.LineageGraph:
        """Retrieve lineage graph for an asset."""
        try:
            async for session in get_session():
                # Query edges where the asset is source or target
                direction = request.direction or "both"
                max_depth = request.depth or 3

                edges_query = select(LineageEdgeModel)
                if direction in ("upstream", "both"):
                    edges_query = edges_query.where(
                        LineageEdgeModel.target_asset_id == request.asset_id
                    )
                if direction in ("downstream", "both"):
                    edges_query = edges_query.union(
                        select(LineageEdgeModel).where(
                            LineageEdgeModel.source_asset_id == request.asset_id
                        )
                    )

                result = await session.execute(edges_query)
                edge_rows = result.scalars().all()

                nodes = {}
                proto_edges = []
                for edge in edge_rows:
                    # Build nodes from edges
                    for asset_id, col in [
                        (edge.source_asset_id, edge.source_column),
                        (edge.target_asset_id, edge.target_column),
                    ]:
                        node_key = f"{asset_id}:{col}" if col else asset_id
                        if node_key not in nodes:
                            nodes[node_key] = metadata_pb2.LineageNode(
                                id=node_key,
                                asset_id=asset_id,
                                column_name=col or "",
                                node_type="column" if col else "table",
                            )

                    proto_edges.append(metadata_pb2.LineageEdge(
                        id=str(edge.id),
                        source_node_id=f"{edge.source_asset_id}:{edge.source_column}" if edge.source_column else edge.source_asset_id,
                        target_node_id=f"{edge.target_asset_id}:{edge.target_column}" if edge.target_column else edge.target_asset_id,
                        edge_type=edge.edge_type or "direct",
                        transformation=edge.transformation or "",
                    ))

                return metadata_pb2.LineageGraph(
                    nodes=list(nodes.values()),
                    edges=proto_edges,
                )
        except Exception as e:
            logger.error("grpc.get_lineage.error", error=str(e))
            await context.abort(grpc.StatusCode.INTERNAL, f"Failed to get lineage: {e}")

    async def GetQualityReport(
        self,
        request: metadata_pb2.GetQualityReportRequest,
        context: grpc.aio.ServicerContext,
    ) -> metadata_pb2.QualityReport:
        """Retrieve the latest quality report for an asset."""
        try:
            async for session in get_session():
                # Get the asset to confirm it exists
                asset_result = await session.execute(
                    select(Asset).where(Asset.id == request.asset_id)
                )
                asset = asset_result.scalar_one_or_none()
                if asset is None:
                    await context.abort(grpc.StatusCode.NOT_FOUND, f"Asset not found: {request.asset_id}")
                    return metadata_pb2.QualityReport()

                # Get quality checks for this asset
                checks_result = await session.execute(
                    select(QualityCheckModel).where(QualityCheckModel.asset_id == request.asset_id)
                )
                checks = checks_result.scalars().all()

                proto_checks = [
                    metadata_pb2.QualityCheck(
                        check_name=c.check_name,
                        check_type=c.check_type,
                        column_name=c.column_name or "",
                        passed=c.passed,
                        score=c.score or 0.0,
                        details=c.details or "",
                        severity=c.severity or "info",
                    )
                    for c in checks
                ]

                overall_score = (
                    sum(c.score for c in proto_checks) / len(proto_checks) if proto_checks else 0.0
                )

                return metadata_pb2.QualityReport(
                    asset_id=request.asset_id,
                    overall_score=overall_score,
                    passed=all(c.passed for c in proto_checks),
                    checks=proto_checks,
                    generated_at=datetime.now(timezone.utc).isoformat(),
                    generated_by="udc-metacatalog",
                )
        except grpc.aio.AbortError:
            raise
        except Exception as e:
            logger.error("grpc.get_quality_report.error", error=str(e))
            await context.abort(grpc.StatusCode.INTERNAL, f"Failed to get quality report: {e}")


def _asset_to_proto(asset: Asset) -> metadata_pb2.DataAsset:
    """Convert a SQLAlchemy Asset model to a protobuf DataAsset message."""
    return metadata_pb2.DataAsset(
        id=str(asset.id),
        name=asset.name or "",
        qualified_name=asset.qualified_name or "",
        source_type=asset.source_type or "",
        source_instance=asset.source_instance or "",
        database_name=asset.database_name or "",
        schema_name=asset.schema_name or "",
        description=asset.description or "",
        tags=list(asset.tags) if asset.tags else [],
        quality_score=asset.quality_score or 0.0,
        owner=asset.owner or "",
        created_at=asset.created_at.isoformat() if asset.created_at else "",
        updated_at=asset.updated_at.isoformat() if asset.updated_at else "",
    )


async def start_grpc_server(port: int | None = None) -> aio.Server:
    """Create and start the gRPC server."""
    grpc_port = port or int(os.environ.get("GRPC_PORT", "50052"))

    server = aio.server()
    metadata_pb2_grpc.add_MetadataServiceServicer_to_server(
        MetadataServiceServicer(), server
    )
    server.add_insecure_port(f"[::]:{grpc_port}")
    await server.start()
    logger.info("grpc.server.started", port=grpc_port)
    return server


async def stop_grpc_server(server: aio.Server) -> None:
    """Gracefully stop the gRPC server."""
    await server.stop(grace=5)
    logger.info("grpc.server.stopped")
