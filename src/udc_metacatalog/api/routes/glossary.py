"""UDC MetaCatalog — Business glossary routes."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from core.models import GlossaryTerm
from core.schemas import GlossaryTermCreate, GlossaryTermResponse

logger = structlog.get_logger(__name__)

router = APIRouter()


class GlossaryTermUpdate(BaseModel):
    """Schema for updating a glossary term."""

    name: str | None = None
    definition: str | None = None
    owner: str | None = None
    aliases: list[str] | None = None


@router.get("/terms")
async def list_terms(
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """List business glossary terms."""
    base_query = select(GlossaryTerm)
    count_query = select(func.count()).select_from(GlossaryTerm)
    if search:
        pattern = f"%{search}%"
        base_query = base_query.where(GlossaryTerm.name.ilike(pattern))
        count_query = count_query.where(GlossaryTerm.name.ilike(pattern))

    total = (await session.execute(count_query)).scalar_one()
    skip = (page - 1) * page_size
    result = await session.execute(base_query.offset(skip).limit(page_size))
    terms = result.scalars().all()
    return {"items": [GlossaryTermResponse.model_validate(t) for t in terms], "total_count": total, "page": page, "page_size": page_size}


@router.post("/terms", response_model=GlossaryTermResponse, status_code=201)
async def create_term(
    body: GlossaryTermCreate,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Create a new business glossary term."""
    term = GlossaryTerm(**body.model_dump())
    session.add(term)
    await session.commit()
    await session.refresh(term)
    logger.info("glossary.term_created", term_id=str(term.id), name=term.name)
    return term


@router.get("/terms/{term_id}", response_model=GlossaryTermResponse)
async def get_term(
    term_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Get a glossary term by ID."""
    result = await session.execute(select(GlossaryTerm).where(GlossaryTerm.id == term_id))
    term = result.scalar_one_or_none()
    if term is None:
        raise HTTPException(status_code=404, detail="Glossary term not found")
    return term


@router.put("/terms/{term_id}", response_model=GlossaryTermResponse)
async def update_term(
    term_id: UUID,
    body: GlossaryTermUpdate,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Update a glossary term."""
    result = await session.execute(select(GlossaryTerm).where(GlossaryTerm.id == term_id))
    term = result.scalar_one_or_none()
    if term is None:
        raise HTTPException(status_code=404, detail="Glossary term not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(term, field, value)
    term.version += 1
    await session.commit()
    await session.refresh(term)
    logger.info("glossary.term_updated", term_id=str(term_id))
    return term


@router.delete("/terms/{term_id}", status_code=204)
async def delete_term(
    term_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a glossary term."""
    result = await session.execute(select(GlossaryTerm).where(GlossaryTerm.id == term_id))
    term = result.scalar_one_or_none()
    if term is None:
        raise HTTPException(status_code=404, detail="Glossary term not found")
    await session.delete(term)
    await session.commit()
    logger.info("glossary.term_deleted", term_id=str(term_id))


@router.get("/formulas")
async def list_formulas(
    session: AsyncSession = Depends(get_session),
) -> Any:
    """List KPI formulas from the formula registry."""
    from core.models import KPIFormula

    result = await session.execute(select(KPIFormula))
    formulas = result.scalars().all()
    return [
        {
            "id": str(f.id),
            "name": f.name,
            "expression": f.expression,
            "description": f.description,
            "format_string": f.format_string,
            "source_columns": f.source_columns,
        }
        for f in formulas
    ]


@router.post("/auto-tag")
async def auto_tag_columns(asset_id: str) -> Any:
    """Auto-tag columns of an asset to glossary terms using LLM."""
    raise NotImplementedError("Auto-tagging not yet implemented")
