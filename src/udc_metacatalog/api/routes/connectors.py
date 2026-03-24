"""UDC MetaCatalog — Connector management routes."""

import uuid
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from core.models import DataAsset

logger = structlog.get_logger(__name__)

router = APIRouter()

_SUPPORTED_SOURCES = {"postgres", "sap", "fabric"}


class ScanRequest(BaseModel):
    """Request body for triggering a source scan."""

    source_type: str = Field(..., pattern="^(postgres|sap|fabric)$")
    source_instance: str
    database_name: str | None = None
    schema_name: str | None = None
    connection_details: dict[str, str] = Field(default_factory=dict)


@router.get("/")
async def list_connectors() -> Any:
    """List all configured data source connectors."""
    return [
        {"id": src, "name": src.title(), "supported": True}
        for src in sorted(_SUPPORTED_SOURCES)
    ]


@router.post("/scan", status_code=201)
async def trigger_scan(
    body: ScanRequest,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Trigger a source scan. Creates asset records synchronously and returns a job ID."""
    job_id = uuid.uuid4()
    qualified_name = f"{body.source_type}://{body.source_instance}"
    if body.database_name:
        qualified_name += f"/{body.database_name}"
    if body.schema_name:
        qualified_name += f"/{body.schema_name}"

    # Check if asset already exists
    existing = await session.execute(
        select(DataAsset).where(DataAsset.qualified_name == qualified_name)
    )
    asset = existing.scalar_one_or_none()
    if asset is None:
        asset = DataAsset(
            name=body.source_instance,
            qualified_name=qualified_name,
            source_type=body.source_type,
            source_instance=body.source_instance,
            database_name=body.database_name,
            schema_name=body.schema_name,
        )
        session.add(asset)
        await session.commit()
        await session.refresh(asset)

    logger.info("connector.scan_triggered", job_id=str(job_id), source_type=body.source_type)
    return {
        "job_id": str(job_id),
        "status": "completed",
        "asset_id": str(asset.id),
        "qualified_name": qualified_name,
    }


@router.get("/{connector_id}/status")
async def get_scan_status(connector_id: str) -> Any:
    """Get the status of the latest scan for a connector."""
    if connector_id not in _SUPPORTED_SOURCES:
        raise HTTPException(status_code=404, detail="Connector not found")
    return {"connector_id": connector_id, "status": "idle", "last_scan": None}
