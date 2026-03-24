"""UDC VisionLens — Authentication middleware (API Key + Bearer Token)."""

import os

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = structlog.get_logger(__name__)

PUBLIC_PATHS: set[str] = {"/health", "/docs", "/openapi.json", "/redoc"}


class AuthMiddleware(BaseHTTPMiddleware):
    """Validate API key or Bearer token on non-public routes."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Check authorization header for protected endpoints.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware or route handler.

        Returns:
            HTTP response from downstream handler or 401/403 error.
        """
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        api_key = request.headers.get("X-API-Key", "")

        expected_api_key = os.getenv("VISIONLENS_API_KEY", "")

        if api_key and api_key == expected_api_key:
            return await call_next(request)

        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ")
            if token and token == os.getenv("VISIONLENS_BEARER_TOKEN", ""):
                return await call_next(request)

        logger.warning("auth_failed", path=request.url.path, method=request.method)
        return Response(status_code=401, content="Unauthorized")
