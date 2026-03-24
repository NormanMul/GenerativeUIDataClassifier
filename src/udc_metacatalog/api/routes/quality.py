"""UDC MetaCatalog — Data quality routes."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from core.models import DataAsset, QualityReportRecord
from core.schemas import QualityCheckResult, QualityReportResponse

logger = structlog.get_logger(__name__)

router = APIRouter()


class QualityReportCreate(BaseModel):
    """Request body for creating a quality report."""

    asset_id: UUID
    overall_score: float = Field(..., ge=0.0, le=1.0)
    passed: bool
    checks: list[QualityCheckResult]
    generated_by: str | None = None
    execution_time_ms: int | None = None


@router.post("/{asset_id}/profile")
async def trigger_profiling(asset_id: UUID) -> Any:
    """Trigger data quality profiling for an asset."""
    raise NotImplementedError("Profiling not yet implemented")


@router.get("/{asset_id}/report", response_model=QualityReportResponse)
async def get_quality_report(
    asset_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Get the latest quality report for an asset."""
    query = (
        select(QualityReportRecord)
        .where(QualityReportRecord.asset_id == asset_id)
        .order_by(QualityReportRecord.created_at.desc())
        .limit(1)
    )
    result = await session.execute(query)
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=404, detail="No quality report found for this asset")
    return report


@router.get("/{asset_id}/history")
async def get_quality_history(
    asset_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Get all quality reports for an asset, ordered descending."""
    query = (
        select(QualityReportRecord)
        .where(QualityReportRecord.asset_id == asset_id)
        .order_by(QualityReportRecord.created_at.desc())
    )
    result = await session.execute(query)
    reports = result.scalars().all()
    return [QualityReportResponse.model_validate(r) for r in reports]


@router.get("/{asset_id}/score")
async def get_quality_score(
    asset_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Get the current quality score for an asset."""
    result = await session.execute(select(DataAsset).where(DataAsset.id == asset_id))
    asset = result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"asset_id": str(asset_id), "quality_score": asset.quality_score}


@router.post("/", response_model=QualityReportResponse, status_code=201)
async def create_quality_report(
    body: QualityReportCreate,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Create a quality report for an asset."""
    # Verify the asset exists
    asset_result = await session.execute(select(DataAsset).where(DataAsset.id == body.asset_id))
    if asset_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    report = QualityReportRecord(
        asset_id=body.asset_id,
        overall_score=body.overall_score,
        passed=body.passed,
        checks=[c.model_dump() for c in body.checks],
        generated_by=body.generated_by,
        execution_time_ms=body.execution_time_ms,
    )
    session.add(report)
    await session.commit()
    await session.refresh(report)
    logger.info("quality.report_created", report_id=str(report.id), asset_id=str(body.asset_id))
    return report


@router.post("/{asset_id}/validate")
async def validate_quality(asset_id: UUID) -> Any:
    """Run quality gate validation checks."""
    raise NotImplementedError("Quality validation not yet implemented")
