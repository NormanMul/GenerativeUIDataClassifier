"""UDC ContextVault — Health check route."""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return service health status."""
    return {
        "status": "ok",
        "service": "udc-contextvault",
        "version": "0.1.0",
    }
