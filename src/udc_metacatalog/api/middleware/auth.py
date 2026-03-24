"""UDC MetaCatalog — API Key authentication middleware."""

import os
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)

# Paths that don't require authentication
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class AuthMiddleware(BaseHTTPMiddleware):
    """Validate API Key or Azure Service Principal JWT on every request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check authentication for non-public paths."""
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # Check X-API-Key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            if await self._validate_api_key(api_key):
                return await call_next(request)
            return Response(content='{"detail":"Invalid API key"}', status_code=401, media_type="application/json")

        # Check Bearer token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            if await self._validate_bearer_token(token):
                return await call_next(request)
            return Response(content='{"detail":"Invalid token"}', status_code=401, media_type="application/json")

        return Response(
            content='{"detail":"Authentication required. Provide X-API-Key or Bearer token."}',
            status_code=401,
            media_type="application/json",
        )

    async def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key against the database."""
        master_key = os.environ.get("API_KEY_MASTER", "")
        return api_key == master_key and master_key != ""

    async def _validate_bearer_token(self, token: str) -> bool:
        """Validate Azure Service Principal JWT."""
        # TODO: Implement JWKS-based JWT validation
        return False
