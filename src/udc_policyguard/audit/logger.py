"""UDC PolicyGuard — Immutable audit log writer."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class AuditEntry:
    """A single audit log entry."""

    agent_id: str
    session_id: str
    action_type: str
    resource: str
    decision: str
    reason: str
    user_role: str
    context: dict[str, Any]
    timestamp: datetime


class AuditLogger:
    """Append-only audit logger backed by PostgreSQL.

    All entries are written via INSERT only — no UPDATE or DELETE
    operations are permitted, ensuring an immutable audit trail.
    Also publishes each entry to Redis channel 'udc:audit' for
    real-time monitoring.
    """

    INSERT_SQL = """
        INSERT INTO audit_log
            (agent_id, session_id, action_type, resource,
             decision, reason, user_role, context, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
    """

    def __init__(
        self,
        pg_pool: Any | None = None,
        redis_client: Any | None = None,
    ) -> None:
        self._pg_pool = pg_pool
        self._redis = redis_client
        self._buffer: list[AuditEntry] = []

    async def log(self, entry: AuditEntry) -> None:
        """Write an audit entry to the append-only log.

        Args:
            entry: The audit entry to persist.
        """
        # Persist to PostgreSQL if pool is available
        if self._pg_pool is not None:
            try:
                async with self._pg_pool.acquire() as conn:
                    await conn.execute(
                        self.INSERT_SQL,
                        entry.agent_id,
                        entry.session_id,
                        entry.action_type,
                        entry.resource,
                        entry.decision,
                        entry.reason,
                        entry.user_role,
                        json.dumps(entry.context, default=str),
                        entry.timestamp,
                    )
            except Exception as exc:
                logger.error("audit_logger.pg_error", error=str(exc))
                self._buffer.append(entry)
        else:
            # Buffer entries when no database is configured
            self._buffer.append(entry)

        # Publish to Redis for real-time monitoring
        if self._redis is not None:
            try:
                payload = json.dumps(
                    {**asdict(entry), "timestamp": entry.timestamp.isoformat()},
                    default=str,
                )
                await self._redis.publish("udc:audit", payload)
            except Exception as exc:
                logger.warning("audit_logger.redis_publish_error", error=str(exc))

        logger.info(
            "audit_logger.logged",
            agent_id=entry.agent_id,
            action=entry.action_type,
            decision=entry.decision,
        )

    def log_sync(self, entry: AuditEntry) -> None:
        """Synchronous convenience method that buffers the entry."""
        self._buffer.append(entry)
        logger.info(
            "audit_logger.buffered",
            agent_id=entry.agent_id,
            action=entry.action_type,
            decision=entry.decision,
        )

    async def flush_buffer(self) -> int:
        """Flush buffered entries to PostgreSQL. Returns count flushed."""
        if not self._buffer or self._pg_pool is None:
            return 0
        flushed = 0
        remaining: list[AuditEntry] = []
        for entry in self._buffer:
            try:
                async with self._pg_pool.acquire() as conn:
                    await conn.execute(
                        self.INSERT_SQL,
                        entry.agent_id,
                        entry.session_id,
                        entry.action_type,
                        entry.resource,
                        entry.decision,
                        entry.reason,
                        entry.user_role,
                        json.dumps(entry.context, default=str),
                        entry.timestamp,
                    )
                flushed += 1
            except Exception:
                remaining.append(entry)
        self._buffer = remaining
        logger.info("audit_logger.flushed", count=flushed, remaining=len(remaining))
        return flushed
