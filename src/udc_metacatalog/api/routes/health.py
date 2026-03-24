"""UDC MetaCatalog — Health check endpoint."""

import os

import structlog
from fastapi import APIRouter, Request

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check(request: Request) -> dict:
    """Return service health status with dependency checks."""
    checks: dict[str, dict] = {}

    # --- PostgreSQL check ---
    try:
        from core.database import _engine

        if _engine is not None:
            async with _engine.connect() as conn:
                await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            checks["postgres"] = {"status": "ok"}
        else:
            checks["postgres"] = {"status": "unavailable", "error": "engine not initialised"}
    except Exception as e:
        checks["postgres"] = {"status": "error", "error": str(e)}

    # --- Redis check ---
    try:
        from core.events import _redis

        if _redis is not None:
            await _redis.ping()
            checks["redis"] = {"status": "ok"}
        else:
            checks["redis"] = {"status": "unavailable", "error": "redis not initialised"}
    except Exception as e:
        checks["redis"] = {"status": "error", "error": str(e)}

    all_ok = all(c["status"] == "ok" for c in checks.values())

    return {
        "status": "ok" if all_ok else "degraded",
        "service": "udc-metacatalog",
        "version": "0.1.0",
        "checks": checks,
    }
