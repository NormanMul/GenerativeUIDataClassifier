"""UDC DesktopAgent — Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return service health status.

    Returns:
        Dictionary with status and service name.
    """
    return {"status": "ok", "service": "udc-desktopagent"}
