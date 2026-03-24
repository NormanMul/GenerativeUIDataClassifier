"""UDC DesktopAgent — FastAPI application with WebSocket support."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from udc_desktopagent.api.middleware.audit import AuditMiddleware
from udc_desktopagent.api.middleware.auth import AuthMiddleware
from udc_desktopagent.api.routes import actions, health, screenshots, tasks

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle.

    Args:
        app: The FastAPI application instance.
    """
    logger.info("desktopagent_starting")
    yield
    logger.info("desktopagent_shutdown")


app = FastAPI(
    title="UDC DesktopAgent",
    description="Containerized desktop automation agent",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(AuditMiddleware)
app.add_middleware(AuthMiddleware)

app.include_router(health.router)
app.include_router(tasks.router)
app.include_router(actions.router)
app.include_router(screenshots.router)
