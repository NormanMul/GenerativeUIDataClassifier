"""UDC ContextVault — PostgreSQL JSONB document store.

Stores full context entries as JSONB documents in PostgreSQL,
providing path-based lookup and full-text search capabilities.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import asyncpg
import structlog

logger = structlog.get_logger(__name__)


def _dsn() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/contextvault",
    )


class PostgresDocumentStore:
    """Persist context entries as JSONB documents in PostgreSQL.

    Each entry is keyed by its virtual filesystem path and stores
    the full content, all compression layers, and arbitrary metadata
    in a single JSONB column for flexible querying.
    """

    def __init__(self) -> None:
        self._pool: asyncpg.Pool | None = None

    async def _get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(dsn=_dsn(), min_size=2, max_size=10)
        return self._pool

    async def store(
        self,
        path: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        layer: str = "l2",
    ) -> dict[str, Any]:
        """Persist a context entry."""
        pool = await self._get_pool()
        doc_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        meta_json = json.dumps(metadata or {})

        await pool.execute(
            """
            INSERT INTO context_documents (id, uri, content, metadata, layer, created_at)
            VALUES ($1, $2, $3, $4::jsonb, $5, $6)
            ON CONFLICT (uri) DO UPDATE
                SET content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    layer = EXCLUDED.layer,
                    created_at = EXCLUDED.created_at
            """,
            doc_id,
            path,
            content,
            meta_json,
            layer,
            now,
        )
        logger.info("document_store.store", path=path, layer=layer)
        return {"id": doc_id, "uri": path, "layer": layer, "created_at": now.isoformat()}

    async def get(self, path: str) -> dict[str, Any] | None:
        """Retrieve a context entry by path or vault:// URI."""
        pool = await self._get_pool()
        row = await pool.fetchrow(
            "SELECT id, uri, content, metadata, layer, created_at FROM context_documents WHERE uri = $1",
            path,
        )
        if row is None:
            return None
        return {
            "id": str(row["id"]),
            "uri": row["uri"],
            "content": row["content"],
            "metadata": json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"],
            "layer": row["layer"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        }

    async def list_documents(
        self,
        layer: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List documents with optional layer filter and pagination."""
        pool = await self._get_pool()
        if layer:
            rows = await pool.fetch(
                "SELECT id, uri, content, metadata, layer, created_at "
                "FROM context_documents WHERE layer = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3",
                layer,
                limit,
                offset,
            )
        else:
            rows = await pool.fetch(
                "SELECT id, uri, content, metadata, layer, created_at "
                "FROM context_documents ORDER BY created_at DESC LIMIT $1 OFFSET $2",
                limit,
                offset,
            )
        return [
            {
                "id": str(r["id"]),
                "uri": r["uri"],
                "content": r["content"],
                "metadata": json.loads(r["metadata"]) if isinstance(r["metadata"], str) else r["metadata"],
                "layer": r["layer"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in rows
        ]

    async def search(self, query: str) -> list[dict[str, Any]]:
        """Full-text search across stored context entries."""
        pool = await self._get_pool()
        rows = await pool.fetch(
            """
            SELECT id, uri, content, metadata, layer, created_at,
                   ts_rank(to_tsvector('english', content), plainto_tsquery('english', $1)) AS rank
            FROM context_documents
            WHERE to_tsvector('english', content) @@ plainto_tsquery('english', $1)
            ORDER BY rank DESC
            LIMIT 20
            """,
            query,
        )
        return [
            {
                "id": str(r["id"]),
                "uri": r["uri"],
                "content": r["content"],
                "metadata": json.loads(r["metadata"]) if isinstance(r["metadata"], str) else r["metadata"],
                "layer": r["layer"],
                "rank": float(r["rank"]),
            }
            for r in rows
        ]

    async def delete(self, path: str) -> None:
        """Delete a context entry by path."""
        pool = await self._get_pool()
        await pool.execute("DELETE FROM context_documents WHERE uri = $1", path)
        logger.info("document_store.delete", path=path)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None
