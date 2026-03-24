"""UDC MetaCatalog — Column-level lineage routes."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from core.models import LineageEdge

logger = structlog.get_logger(__name__)

router = APIRouter()


class LineageEdgeCreate(BaseModel):
    """Request body for creating a lineage edge."""

    source_asset_id: UUID
    source_column: str = Field(..., min_length=1)
    target_asset_id: UUID
    target_column: str = Field(..., min_length=1)
    edge_type: str = "direct"
    transformation: str | None = None


@router.get("/{asset_id}")
async def get_lineage(
    asset_id: UUID,
    column_name: str | None = Query(None),
    direction: str = Query("both", regex="^(upstream|downstream|both)$"),
    depth: int = Query(3, ge=1, le=10),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Get lineage graph for an asset or specific column."""
    if direction == "upstream":
        query = select(LineageEdge).where(LineageEdge.target_asset_id == asset_id)
    elif direction == "downstream":
        query = select(LineageEdge).where(LineageEdge.source_asset_id == asset_id)
    else:
        query = select(LineageEdge).where(
            or_(LineageEdge.source_asset_id == asset_id, LineageEdge.target_asset_id == asset_id)
        )
    if column_name:
        query = query.where(
            or_(LineageEdge.source_column == column_name, LineageEdge.target_column == column_name)
        )
    result = await session.execute(query)
    edges = result.scalars().all()
    return [
        {
            "id": str(e.id),
            "source_asset_id": str(e.source_asset_id),
            "source_column": e.source_column,
            "target_asset_id": str(e.target_asset_id),
            "target_column": e.target_column,
            "edge_type": e.edge_type,
            "transformation": e.transformation,
            "created_at": e.created_at.isoformat(),
        }
        for e in edges
    ]


@router.post("/edges", status_code=201)
async def register_lineage_edge(
    body: LineageEdgeCreate,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Register a lineage edge between two columns."""
    edge = LineageEdge(
        source_asset_id=body.source_asset_id,
        source_column=body.source_column,
        target_asset_id=body.target_asset_id,
        target_column=body.target_column,
        edge_type=body.edge_type,
        transformation=body.transformation,
    )
    session.add(edge)
    await session.commit()
    await session.refresh(edge)
    logger.info("lineage.edge_created", edge_id=str(edge.id))
    return {
        "id": str(edge.id),
        "source_asset_id": str(edge.source_asset_id),
        "source_column": edge.source_column,
        "target_asset_id": str(edge.target_asset_id),
        "target_column": edge.target_column,
        "edge_type": edge.edge_type,
        "transformation": edge.transformation,
        "created_at": edge.created_at.isoformat(),
    }
