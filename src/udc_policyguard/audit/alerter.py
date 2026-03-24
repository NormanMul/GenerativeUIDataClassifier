"""UDC PolicyGuard — Policy violation alerting."""

import json
from datetime import datetime, timezone
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

# Default thresholds
_LOW_TRUST_THRESHOLD = 300
_CONSECUTIVE_DENIAL_LIMIT = 3
_SENSITIVE_RESOURCE_PREFIXES = ("pii:", "restricted:", "confidential:")


class PolicyAlerter:
    """Send alerts when policy violations occur.

    Dispatches notifications via Redis pub/sub when agents
    violate governance policies.  Checks for:
    - Trust score dropping below threshold (300)
    - Consecutive denials exceeding limit (3)
    - Sensitive resource access
    """

    def __init__(
        self,
        redis_client: Any | None = None,
        *,
        low_trust_threshold: int = _LOW_TRUST_THRESHOLD,
        max_consecutive_denials: int = _CONSECUTIVE_DENIAL_LIMIT,
    ) -> None:
        self._redis = redis_client
        self._low_trust_threshold = low_trust_threshold
        self._max_consecutive_denials = max_consecutive_denials
        # Track consecutive denials per agent
        self._consecutive_denials: dict[str, int] = {}

    def check_alerts(
        self,
        agent_id: str,
        decision: str,
        resource: str,
        trust_score: int,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Check for alert conditions after a policy evaluation.

        Returns a list of alerts triggered (may be empty).
        """
        alerts: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc).isoformat()

        # --- consecutive denial tracking ---
        if decision == "deny":
            self._consecutive_denials[agent_id] = (
                self._consecutive_denials.get(agent_id, 0) + 1
            )
        else:
            self._consecutive_denials[agent_id] = 0

        # Alert: trust score below threshold
        if trust_score < self._low_trust_threshold:
            alerts.append({
                "type": "low_trust_score",
                "severity": "high",
                "agent_id": agent_id,
                "trust_score": trust_score,
                "threshold": self._low_trust_threshold,
                "message": (
                    f"Agent '{agent_id}' trust score ({trust_score}) "
                    f"dropped below threshold ({self._low_trust_threshold})"
                ),
                "timestamp": now,
            })

        # Alert: consecutive denials exceeded
        streak = self._consecutive_denials.get(agent_id, 0)
        if streak > self._max_consecutive_denials:
            alerts.append({
                "type": "consecutive_denials",
                "severity": "high",
                "agent_id": agent_id,
                "consecutive_count": streak,
                "message": (
                    f"Agent '{agent_id}' denied {streak} consecutive times"
                ),
                "timestamp": now,
            })

        # Alert: sensitive resource access
        if any(resource.startswith(prefix) for prefix in _SENSITIVE_RESOURCE_PREFIXES):
            alerts.append({
                "type": "sensitive_resource_access",
                "severity": "medium",
                "agent_id": agent_id,
                "resource": resource,
                "decision": decision,
                "message": (
                    f"Agent '{agent_id}' accessed sensitive resource '{resource}'"
                ),
                "timestamp": now,
            })

        # Publish each alert
        for alert in alerts:
            self._send_alert(alert)

        return alerts

    def alert(self, violation: dict[str, Any]) -> None:
        """Send webhook and email alerts for a policy violation.

        Args:
            violation: Details of the policy violation including
                agent_id, action_type, resource, and violated policies.
        """
        alert_payload = {
            "type": "policy_violation",
            "severity": "high",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **violation,
        }
        self._send_alert(alert_payload)

    def _send_alert(self, alert: dict[str, Any]) -> None:
        """Publish alert to Redis channel 'udc:alerts'."""
        logger.warning(
            "alerter.alert_triggered",
            alert_type=alert.get("type"),
            severity=alert.get("severity"),
            agent_id=alert.get("agent_id"),
        )
        if self._redis is not None:
            try:
                payload = json.dumps(alert, default=str)
                self._redis.publish("udc:alerts", payload)
            except Exception as exc:
                logger.error("alerter.redis_publish_error", error=str(exc))
