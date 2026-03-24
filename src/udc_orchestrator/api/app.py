"""UDC Orchestrator — FastAPI application with lifespan management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from udc_orchestrator.api.middleware.audit import AuditMiddleware
from udc_orchestrator.api.middleware.auth import AuthMiddleware
from udc_orchestrator.api.routes import chat, health, workflows

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: initialize tool registry, load workflows, init Redis."""
    logger.info("orchestrator.startup", service="udc-orchestrator")

    # Initialize tool registry with all UDC subsystem tools
    from udc_orchestrator.core.tool_registry import ToolRegistry

    app.state.tool_registry = ToolRegistry()
    logger.info("orchestrator.tool_registry.initialized")

    # Load workflow definitions from YAML
    from udc_orchestrator.core.workflow_engine import WorkflowEngine

    app.state.workflow_engine = WorkflowEngine()
    logger.info("orchestrator.workflow_engine.initialized")

    # Initialize Redis connection for caching and state
    import redis.asyncio as aioredis

    app.state.redis = aioredis.from_url(
        "redis://localhost:6379", decode_responses=True
    )
    logger.info("orchestrator.redis.initialized")

    # Start Redis Pub/Sub event listeners
    from udc_orchestrator.events.handlers import start_event_listeners

    app.state.event_task = await start_event_listeners(app.state.redis)

    yield

    # Shutdown
    if hasattr(app.state, "event_task") and app.state.event_task:
        app.state.event_task.cancel()
    await app.state.redis.close()
    logger.info("orchestrator.shutdown", service="udc-orchestrator")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="UDC Orchestrator",
        description="Copilot SDK integration and workflow engine service",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Middleware (order matters — outermost first)
    app.add_middleware(AuditMiddleware)
    app.add_middleware(AuthMiddleware)

    # Routers
    app.include_router(health.router, tags=["health"])
    app.include_router(workflows.router, prefix="/api/v1", tags=["workflows"])
    app.include_router(chat.router, prefix="/api/v1", tags=["chat"])

    return app


app = create_app()
