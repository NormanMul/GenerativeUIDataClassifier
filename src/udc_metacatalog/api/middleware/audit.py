"""UDC MetaCatalog — Request audit logging middleware."""

import time
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """Log every request with structured JSON for audit trail."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request details and timing."""
        start_time = time.monotonic()

        response = await call_next(request)

        duration_ms = (time.monotonic() - start_time) * 1000
        logger.info(
            "http.request",
            service="metacatalog",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            client_ip=request.client.host if request.client else "unknown",
        )

        return response
