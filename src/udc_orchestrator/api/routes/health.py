"""UDC Orchestrator — Health check endpoint."""

import os

import grpc
import structlog
from fastapi import APIRouter, Request
from grpc import aio

logger = structlog.get_logger(__name__)

router = APIRouter()

# gRPC service endpoints to probe (name → host_env:port)
_GRPC_DEPENDENCIES: dict[str, tuple[str, int]] = {
    "metacatalog": (os.environ.get("METACATALOG_GRPC_HOST", "localhost"), 50052),
    "classifier": (os.environ.get("CLASSIFIER_GRPC_HOST", "localhost"), 50051),
    "contextvault": (os.environ.get("CONTEXTVAULT_GRPC_HOST", "localhost"), 50053),
    "visionlens": (os.environ.get("VISIONLENS_GRPC_HOST", "localhost"), 50054),
    "desktopagent": (os.environ.get("DESKTOPAGENT_GRPC_HOST", "localhost"), 50055),
    "policyguard": (os.environ.get("POLICYGUARD_GRPC_HOST", "localhost"), 50056),
}


@router.get("/health")
async def health_check(request: Request) -> dict:
    """Return service health status with dependency checks."""
    checks: dict[str, dict] = {}

    # --- Redis check ---
    try:
        redis = request.app.state.redis
        if redis is not None:
            await redis.ping()
            checks["redis"] = {"status": "ok"}
        else:
            checks["redis"] = {"status": "unavailable", "error": "redis not initialised"}
    except Exception as e:
        checks["redis"] = {"status": "error", "error": str(e)}

    # --- gRPC dependency checks (connectivity only) ---
    for name, (host, port) in _GRPC_DEPENDENCIES.items():
        try:
            channel = aio.insecure_channel(f"{host}:{port}")
            # Check channel connectivity with a short deadline
            await channel.channel_ready()
            checks[f"grpc_{name}"] = {"status": "ok"}
            await channel.close()
        except Exception:
            checks[f"grpc_{name}"] = {"status": "unreachable", "target": f"{host}:{port}"}

    all_ok = all(c["status"] == "ok" for c in checks.values())

    return {
        "status": "ok" if all_ok else "degraded",
        "service": "udc-orchestrator",
        "version": "0.1.0",
        "checks": checks,
    }
