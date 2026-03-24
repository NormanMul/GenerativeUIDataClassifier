"""UDC PolicyGuard — FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
from fastapi import FastAPI

from udc_policyguard.api.middleware.audit import AuditMiddleware
from udc_policyguard.api.middleware.auth import AuthMiddleware
from udc_policyguard.api.routes import audit, evaluate, health, policies

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: init DB, load policies, init Redis."""
    logger.info("policyguard.startup", status="initializing")

    # Initialize database connection
    logger.info("policyguard.db", status="connecting")

    # Load policy definitions
    logger.info("policyguard.policies", status="loading")

    # Initialize Redis for caching / rate limiting
    logger.info("policyguard.redis", status="connecting")

    logger.info("policyguard.startup", status="ready")
    yield

    # Shutdown
    logger.info("policyguard.shutdown", status="cleaning_up")


app = FastAPI(
    title="UDC PolicyGuard",
    description="Governance, policy enforcement, and audit service",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(AuditMiddleware)
app.add_middleware(AuthMiddleware)

app.include_router(health.router, tags=["health"])
app.include_router(policies.router, prefix="/policies", tags=["policies"])
app.include_router(evaluate.router, prefix="/evaluate", tags=["evaluate"])
app.include_router(audit.router, prefix="/audit", tags=["audit"])
