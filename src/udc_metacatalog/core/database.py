"""UDC MetaCatalog — Async PostgreSQL database connection pool."""

import os
from typing import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.models import Base

logger = structlog.get_logger(__name__)

_engine = None
_session_factory = None


def _get_database_url() -> str:
    """Build PostgreSQL async connection URL from environment variables."""
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "udc")
    user = os.environ.get("POSTGRES_USER", "udc_admin")
    password = os.environ.get("POSTGRES_PASSWORD", "")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


async def init_db() -> None:
    """Initialize the database engine and create tables."""
    global _engine, _session_factory

    url = _get_database_url()
    _engine = create_async_engine(url, pool_size=20, max_overflow=10, echo=False)
    _session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

    # Create tables (use Alembic in production)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("database.initialized", host=os.environ.get("POSTGRES_HOST", "localhost"))


async def close_db() -> None:
    """Close the database engine."""
    global _engine
    if _engine:
        await _engine.dispose()
        logger.info("database.closed")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session."""
    if _session_factory is None:
        msg = "Database not initialized. Call init_db() first."
        raise RuntimeError(msg)
    async with _session_factory() as session:
        yield session
