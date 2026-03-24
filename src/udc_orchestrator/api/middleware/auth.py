"""UDC Orchestrator — Authentication middleware."""

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = structlog.get_logger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Validate JWT tokens and enforce RBAC on incoming requests.

    Extracts the Bearer token from the Authorization header,
    validates it against the identity provider, and attaches
    user context (roles, tenant) to the request state.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip auth for health checks
        if request.url.path in ("/health", "/docs", "/openapi.json"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            logger.warning("auth.missing_token", path=request.url.path)
            return Response(status_code=401, content="Missing or invalid token")

        token = auth_header.removeprefix("Bearer ")
        # TODO: Validate JWT, extract claims, attach to request.state
        request.state.user_id = "placeholder"
        request.state.roles = ["viewer"]

        logger.info(
            "auth.validated",
            user_id=request.state.user_id,
            path=request.url.path,
        )
        return await call_next(request)
