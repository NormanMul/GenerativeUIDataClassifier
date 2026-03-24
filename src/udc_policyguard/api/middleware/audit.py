"""UDC PolicyGuard — Audit logging middleware."""

import time
from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__)

SERVICE_NAME = "policyguard"


class AuditMiddleware(BaseHTTPMiddleware):
    """Log all requests for audit compliance."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Record request metadata to the audit log."""
        start = time.perf_counter()
        request_meta: dict[str, Any] = {
            "service": SERVICE_NAME,
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else "unknown",
        }

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "audit.request",
            **request_meta,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        return response
