"""UDC VisionLens — FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from udc_visionlens.api.middleware.audit import AuditMiddleware
from udc_visionlens.api.middleware.auth import AuthMiddleware
from udc_visionlens.api.routes import detect, health, parse

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle."""
    logger.info("visionlens_starting")
    yield
    logger.info("visionlens_stopping")


app = FastAPI(
    title="UDC VisionLens",
    description="Screen parsing and UI element detection service",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(AuditMiddleware)
app.add_middleware(AuthMiddleware)

app.include_router(health.router)
app.include_router(parse.router)
app.include_router(detect.router)
