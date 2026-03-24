"""UDC MetaCatalog — Semantic search routes."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from core.models import DataAsset
from core.schemas import DataAssetResponse

router = APIRouter()


@router.get("/")
async def search_metadata(
    q: str = Query(..., description="Search query"),
    top_k: int = Query(10, ge=1, le=100),
    source_type: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Search across all metadata using full-text ILIKE search."""
    pattern = f"%{q}%"
    query = select(DataAsset).where(
        or_(
            DataAsset.name.ilike(pattern),
            DataAsset.qualified_name.ilike(pattern),
            DataAsset.description.ilike(pattern),
            DataAsset.tags.any(q),
        )
    )
    if source_type:
        query = query.where(DataAsset.source_type == source_type)
    query = query.limit(top_k)
    result = await session.execute(query)
    assets = result.scalars().all()
    return [DataAssetResponse.model_validate(a) for a in assets]
