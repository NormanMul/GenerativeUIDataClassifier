"""UDC PolicyGuard — Agent trust scoring system."""

import time
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class TrustScore:
    """Trust score for an agent within a session."""

    agent_id: str
    session_id: str
    score: int
    total_successes: int
    total_violations: int


@dataclass
class _ScoreRecord:
    """Internal mutable record for tracking an agent's trust state."""

    score: int = 500
    total_successes: int = 0
    total_violations: int = 0
    last_updated: float = 0.0


class TrustScorer:
    """Track and compute trust scores for agents.

    Trust score ranges from 0–1000, starting at 500.
    Each successful action adds +10, each violation subtracts -50.
    """

    DEFAULT_SCORE: int = 500
    SUCCESS_DELTA: int = 10
    VIOLATION_DELTA: int = -50
    MIN_SCORE: int = 0
    MAX_SCORE: int = 1000

    def __init__(self, redis_client: Any | None = None) -> None:
        self._scores: dict[tuple[str, str], _ScoreRecord] = {}
        self._redis = redis_client

    def _key(self, agent_id: str, session_id: str) -> tuple[str, str]:
        return (agent_id, session_id)

    def _get_record(self, agent_id: str, session_id: str) -> _ScoreRecord:
        key = self._key(agent_id, session_id)
        if key not in self._scores:
            # Try loading from Redis cache if available
            if self._redis is not None:
                redis_key = f"udc:trust:{agent_id}:{session_id}"
                try:
                    cached = self._redis.hgetall(redis_key)
                    if cached:
                        record = _ScoreRecord(
                            score=int(cached.get(b"score", self.DEFAULT_SCORE)),
                            total_successes=int(cached.get(b"successes", 0)),
                            total_violations=int(cached.get(b"violations", 0)),
                        )
                        self._scores[key] = record
                        return record
                except Exception:
                    logger.warning("trust_scorer.redis_read_failed", agent_id=agent_id)
            self._scores[key] = _ScoreRecord()
        return self._scores[key]

    def _persist(self, agent_id: str, session_id: str, record: _ScoreRecord) -> None:
        if self._redis is None:
            return
        redis_key = f"udc:trust:{agent_id}:{session_id}"
        try:
            self._redis.hset(redis_key, mapping={
                "score": record.score,
                "successes": record.total_successes,
                "violations": record.total_violations,
            })
            self._redis.expire(redis_key, 86400)  # 24h TTL
        except Exception:
            logger.warning("trust_scorer.redis_write_failed", agent_id=agent_id)

    def get_score(self, agent_id: str, session_id: str) -> TrustScore:
        """Retrieve the current trust score for an agent/session.

        Args:
            agent_id: Identifier of the agent.
            session_id: Current session identifier.

        Returns:
            Current TrustScore.
        """
        record = self._get_record(agent_id, session_id)
        return TrustScore(
            agent_id=agent_id,
            session_id=session_id,
            score=record.score,
            total_successes=record.total_successes,
            total_violations=record.total_violations,
        )

    def record_success(self, agent_id: str, session_id: str) -> None:
        """Record a successful action, increasing the trust score by +10.

        Args:
            agent_id: Identifier of the agent.
            session_id: Current session identifier.
        """
        record = self._get_record(agent_id, session_id)
        record.total_successes += 1
        record.score = min(self.MAX_SCORE, record.score + self.SUCCESS_DELTA)
        record.last_updated = time.monotonic()
        self._persist(agent_id, session_id, record)
        logger.debug(
            "trust_scorer.success",
            agent_id=agent_id,
            new_score=record.score,
        )

    def record_violation(self, agent_id: str, session_id: str) -> None:
        """Record a policy violation, decreasing the trust score by -50.

        Args:
            agent_id: Identifier of the agent.
            session_id: Current session identifier.
        """
        record = self._get_record(agent_id, session_id)
        record.total_violations += 1
        record.score = max(self.MIN_SCORE, record.score + self.VIOLATION_DELTA)
        record.last_updated = time.monotonic()
        self._persist(agent_id, session_id, record)
        logger.info(
            "trust_scorer.violation",
            agent_id=agent_id,
            new_score=record.score,
        )
