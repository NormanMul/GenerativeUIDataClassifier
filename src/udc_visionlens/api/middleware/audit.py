"""UDC VisionLens — Audit logging middleware."""

import time

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = structlog.get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests with timing and status information."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Record request metadata and response timing for audit trail.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware or route handler.

        Returns:
            HTTP response from downstream handler.
        """
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "request_completed",
            service="visionlens",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )
        return response
