"""UDC MetaCatalog — FastAPI Application."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI

from api.routes import assets, connectors, glossary, health, lineage, quality, search
from api.middleware.auth import AuthMiddleware
from api.middleware.audit import AuditMiddleware

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown."""
    logger.info("metacatalog.starting", version="0.1.0")
    # Startup: initialize database pool, Redis, scheduler
    from core.database import init_db
    from core.events import init_event_bus, _redis

    await init_db()
    await init_event_bus()

    # Start gRPC server alongside FastAPI
    from grpc_server import start_grpc_server, stop_grpc_server

    grpc_server = await start_grpc_server()
    app.state.grpc_server = grpc_server

    # Start Redis Pub/Sub event listeners
    from events.handlers import start_event_listeners
    from core.events import _redis as event_redis

    if event_redis is not None:
        app.state.event_task = await start_event_listeners(event_redis)

    logger.info("metacatalog.started")
    yield
    # Shutdown: close connections
    from core.database import close_db
    from core.events import close_event_bus

    # Stop event listeners
    if hasattr(app.state, "event_task") and app.state.event_task:
        app.state.event_task.cancel()

    # Stop gRPC server
    if hasattr(app.state, "grpc_server"):
        await stop_grpc_server(app.state.grpc_server)

    await close_event_bus()
    await close_db()
    logger.info("metacatalog.stopped")


app = FastAPI(
    title="UDC MetaCatalog",
    description="Metadata catalog, lineage, data quality, and business glossary for the UDC Enterprise Platform.",
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware (order matters: outermost first)
app.add_middleware(AuditMiddleware)
app.add_middleware(AuthMiddleware)

# Routes
app.include_router(health.router)
app.include_router(assets.router, prefix="/assets", tags=["Assets"])
app.include_router(lineage.router, prefix="/lineage", tags=["Lineage"])
app.include_router(glossary.router, prefix="/glossary", tags=["Glossary"])
app.include_router(quality.router, prefix="/quality", tags=["Quality"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(connectors.router, prefix="/connectors", tags=["Connectors"])
