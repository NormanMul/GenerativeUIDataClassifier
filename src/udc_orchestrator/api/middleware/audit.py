"""UDC Orchestrator — Audit logging middleware."""

import time

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = structlog.get_logger(__name__)

SERVICE_NAME = "orchestrator"


class AuditMiddleware(BaseHTTPMiddleware):
    """Log all API requests with timing, user context, and response status."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.perf_counter()

        user_id = getattr(request.state, "user_id", "anonymous")

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "audit.request",
            service=SERVICE_NAME,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            user_id=user_id,
        )

        return response
