"""UDC ContextVault — FastAPI Application."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI

from api.middleware.auth import AuthMiddleware
from api.middleware.audit import AuditMiddleware
from api.routes import context, health, sessions

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown.

    Initialises the database connection pool, Redis cache, and
    vector store on startup and tears them down on shutdown.
    """
    logger.info("contextvault.starting", version="0.1.0")

    # Startup: initialise storage backends
    from storage.vector_store import ChromaDBAdapter
    from storage.document_store import PostgresDocumentStore
    from storage.cache import RedisContextCache

    app.state.vector_store = ChromaDBAdapter()
    app.state.document_store = PostgresDocumentStore()
    app.state.cache = RedisContextCache()

    logger.info("contextvault.started")
    yield

    # Shutdown: close connections
    logger.info("contextvault.stopping")
    logger.info("contextvault.stopped")


app = FastAPI(
    title="UDC ContextVault",
    description="Tiered context memory service for AI agents — virtual filesystem, layered compression, and session management.",
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware (order matters: outermost first)
app.add_middleware(AuditMiddleware)
app.add_middleware(AuthMiddleware)

# Routes
app.include_router(health.router)
app.include_router(context.router, prefix="/context", tags=["Context"])
app.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
