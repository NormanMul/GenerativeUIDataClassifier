"""UDC VisionLens — Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return service health status.

    Returns:
        Dictionary with service name and status.
    """
    return {"status": "ok", "service": "udc-visionlens"}
