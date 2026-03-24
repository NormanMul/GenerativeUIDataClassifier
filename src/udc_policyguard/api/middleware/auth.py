"""UDC PolicyGuard — Authentication middleware."""

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = structlog.get_logger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Validate authentication tokens on incoming requests."""

    SKIP_PATHS: set[str] = {"/health", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Check authorization header for non-exempt paths."""
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning("auth.missing_token", path=request.url.path)
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid authorization token"},
            )

        # Token validation placeholder
        request.state.user_id = "anonymous"
        request.state.roles = []

        return await call_next(request)
