"""UDC MetaCatalog — Data asset CRUD routes."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_session
from core.models import ColumnMeta, DataAsset
from core.schemas import DataAssetCreate, DataAssetResponse, DataAssetUpdate, PaginatedResponse

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=DataAssetResponse, status_code=201)
async def register_asset(
    asset: DataAssetCreate,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Register a new data asset in the catalog."""
    columns_data = asset.columns
    asset_dict = asset.model_dump(exclude={"columns"})
    db_asset = DataAsset(**asset_dict)
    for col in columns_data:
        db_asset.columns.append(ColumnMeta(**col.model_dump()))
    session.add(db_asset)
    await session.commit()
    await session.refresh(db_asset, attribute_names=["columns"])
    logger.info("asset.created", asset_id=str(db_asset.id), name=db_asset.name)
    return db_asset


@router.get("/", response_model=PaginatedResponse)
async def list_assets(
    source_type: str | None = Query(None, description="Filter by source type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """List all registered data assets with optional filtering."""
    base_query = select(DataAsset)
    count_query = select(func.count()).select_from(DataAsset)
    if source_type:
        base_query = base_query.where(DataAsset.source_type == source_type)
        count_query = count_query.where(DataAsset.source_type == source_type)

    total = (await session.execute(count_query)).scalar_one()
    skip = (page - 1) * page_size
    query = base_query.options(selectinload(DataAsset.columns)).offset(skip).limit(page_size)
    result = await session.execute(query)
    assets = result.scalars().all()
    return PaginatedResponse(items=assets, total_count=total, page=page, page_size=page_size)


@router.get("/{asset_id}", response_model=DataAssetResponse)
async def get_asset(
    asset_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Get a specific data asset by ID."""
    query = select(DataAsset).where(DataAsset.id == asset_id).options(selectinload(DataAsset.columns))
    result = await session.execute(query)
    asset = result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.put("/{asset_id}", response_model=DataAssetResponse)
async def update_asset(
    asset_id: UUID,
    asset: DataAssetUpdate,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Update an existing data asset."""
    query = select(DataAsset).where(DataAsset.id == asset_id).options(selectinload(DataAsset.columns))
    result = await session.execute(query)
    db_asset = result.scalar_one_or_none()
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    for field, value in asset.model_dump(exclude_none=True).items():
        setattr(db_asset, field, value)
    await session.commit()
    await session.refresh(db_asset, attribute_names=["columns"])
    logger.info("asset.updated", asset_id=str(asset_id))
    return db_asset


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(
    asset_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a data asset."""
    query = select(DataAsset).where(DataAsset.id == asset_id)
    result = await session.execute(query)
    db_asset = result.scalar_one_or_none()
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    await session.delete(db_asset)
    await session.commit()
    logger.info("asset.deleted", asset_id=str(asset_id))
