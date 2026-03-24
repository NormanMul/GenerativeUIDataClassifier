"""UDC PolicyGuard — Deterministic policy evaluation engine."""

import re
import time
from dataclasses import dataclass, field
from typing import Any

import structlog

from .policy_store import PolicyStore

logger = structlog.get_logger(__name__)


@dataclass
class PolicyDecision:
    """Result of a policy evaluation."""

    allowed: bool
    decision: str
    reason: str
    violated_policies: list[str] = field(default_factory=list)
    evaluation_time_ms: float = 0.0


# ---- condition evaluation helpers (pure functions, no I/O) ---------

def _eval_condition(operator: str, context_value: Any, rule_value: Any) -> bool:
    """Evaluate a single condition operator."""
    if operator == "equals":
        return context_value == rule_value
    if operator == "not_equals":
        return context_value != rule_value
    if operator == "in":
        return context_value in rule_value
    if operator == "not_in":
        return context_value not in rule_value
    if operator == "greater_than":
        return float(context_value) > float(rule_value)
    if operator == "less_than":
        return float(context_value) < float(rule_value)
    if operator == "regex_match":
        return bool(re.search(str(rule_value), str(context_value)))
    if operator == "contains":
        return rule_value in context_value
    return False


class PolicyEngine:
    """Deterministic policy evaluation engine.

    Evaluates agent actions against loaded policies with a target
    latency of <1ms. Checks include:
    - Action type allowlist per agent role
    - Data sensitivity classification enforcement
    - Rate limiting per agent
    - PII access control
    """

    def __init__(self, policy_store: PolicyStore) -> None:
        self._store = policy_store

    # ----------------------------------------------------------------
    # core evaluation
    # ----------------------------------------------------------------

    def evaluate(
        self,
        agent_id: str,
        session_id: str,
        action_type: str,
        resource: str,
        context: dict[str, Any],
        user_role: str,
    ) -> PolicyDecision:
        """Evaluate an action against all loaded policies.

        Args:
            agent_id: Identifier of the requesting agent.
            session_id: Current session identifier.
            action_type: The action being attempted (read, write, delete, etc.).
            resource: Target resource path or identifier.
            context: Additional context for evaluation.
            user_role: Role of the user/agent initiating the action.

        Returns:
            PolicyDecision with allow/deny, reason, and any violated policies.
        """
        t0 = time.perf_counter_ns()
        violated: list[str] = []
        deny_reasons: list[str] = []

        eval_ctx: dict[str, Any] = {
            **context,
            "agent_id": agent_id,
            "session_id": session_id,
            "action_type": action_type,
            "resource": resource,
            "user_role": user_role,
        }

        for policy in self._store.get_all():
            violation = self._check_policy(policy, eval_ctx)
            if violation is not None:
                violated.append(policy["name"])
                deny_reasons.append(violation)

        elapsed_ms = (time.perf_counter_ns() - t0) / 1_000_000

        if violated:
            reason = "; ".join(deny_reasons)
            logger.info(
                "policy_engine.denied",
                agent_id=agent_id,
                action=action_type,
                resource=resource,
                violated=violated,
                elapsed_ms=elapsed_ms,
            )
            return PolicyDecision(
                allowed=False,
                decision="deny",
                reason=reason,
                violated_policies=violated,
                evaluation_time_ms=elapsed_ms,
            )

        logger.debug(
            "policy_engine.allowed",
            agent_id=agent_id,
            action=action_type,
            elapsed_ms=elapsed_ms,
        )
        return PolicyDecision(
            allowed=True,
            decision="allow",
            reason="All policies passed",
            violated_policies=[],
            evaluation_time_ms=elapsed_ms,
        )

    # ----------------------------------------------------------------
    # per-policy checkers
    # ----------------------------------------------------------------

    def _check_policy(
        self, policy: dict[str, Any], ctx: dict[str, Any]
    ) -> str | None:
        """Return a denial reason string if this policy is violated, else None."""
        rule_type = policy.get("rule_type", "")
        rules = policy.get("rules", {})

        handler = self._RULE_HANDLERS.get(rule_type)
        if handler is not None:
            return handler(self, rules, ctx)
        return None

    # ---- action_allowlist -------------------------------------------

    def _check_action_allowlist(
        self, rules: dict, ctx: dict[str, Any]
    ) -> str | None:
        agent_type = rules.get("agent_type")
        if agent_type and agent_type not in ctx.get("agent_id", ""):
            return None  # policy does not apply to this agent
        denied = rules.get("denied_actions", [])
        if ctx.get("action_type") in denied:
            return rules.get("reason", f"Action '{ctx['action_type']}' is denied")
        return None

    # ---- environment_restriction ------------------------------------

    def _check_environment_restriction(
        self, rules: dict, ctx: dict[str, Any]
    ) -> str | None:
        agent_type = rules.get("agent_type")
        if agent_type and agent_type not in ctx.get("agent_id", ""):
            return None
        env = ctx.get("environment", "")
        denied_envs = rules.get("denied_environments", [])
        denied_actions = rules.get("denied_actions", [])
        if env in denied_envs and ctx.get("action_type") in denied_actions:
            return rules.get("reason", f"Action denied in environment '{env}'")
        return None

    # ---- data_access (PII) ------------------------------------------

    def _check_data_access(
        self, rules: dict, ctx: dict[str, Any]
    ) -> str | None:
        pii_fields = rules.get("pii_fields", [])
        accessed_fields = ctx.get("fields", [])
        touching_pii = [f for f in accessed_fields if f in pii_fields]
        if not touching_pii:
            return None
        required_role = rules.get("require_role")
        if required_role and ctx.get("user_role") != required_role:
            return f"PII access requires role '{required_role}'"
        return None

    # ---- data_classification (sensitivity levels) --------------------

    def _check_data_classification(
        self, rules: dict, ctx: dict[str, Any]
    ) -> str | None:
        sensitivity = ctx.get("sensitivity_level", "public")
        levels = rules.get("levels", {})
        level_cfg = levels.get(sensitivity)
        if level_cfg is None:
            return None
        min_trust = level_cfg.get("min_trust_score", 0)
        trust_score = ctx.get("trust_score", 0)
        if trust_score < min_trust:
            return (
                f"Trust score {trust_score} below minimum {min_trust} "
                f"for sensitivity '{sensitivity}'"
            )
        required_role = level_cfg.get("require_role")
        if required_role and ctx.get("user_role") != required_role:
            return (
                f"Role '{ctx.get('user_role')}' cannot access "
                f"'{sensitivity}' data (requires '{required_role}')"
            )
        return None

    # ---- data_export ------------------------------------------------

    def _check_data_export(
        self, rules: dict, ctx: dict[str, Any]
    ) -> str | None:
        if ctx.get("action_type") != "export":
            return None
        row_count = ctx.get("row_count", 0)
        max_rows = rules.get("max_rows_per_export", float("inf"))
        if row_count > max_rows:
            return f"Export of {row_count} rows exceeds limit of {max_rows}"
        fmt = ctx.get("export_format", "")
        blocked = rules.get("blocked_formats", [])
        if fmt in blocked:
            return f"Export format '{fmt}' is blocked"
        return None

    # ---- rate_limit -------------------------------------------------

    def _check_rate_limit(
        self, rules: dict, ctx: dict[str, Any]
    ) -> str | None:
        actions_this_minute = ctx.get("actions_this_minute", 0)
        limit = rules.get("max_actions_per_minute", float("inf"))
        if actions_this_minute >= limit:
            return f"Rate limit exceeded: {actions_this_minute}/{limit} per minute"
        return None

    # ---- quality_gate -----------------------------------------------

    def _check_quality_gate(
        self, rules: dict, ctx: dict[str, Any]
    ) -> str | None:
        metric = rules.get("metric")
        threshold = rules.get("threshold_percent")
        if metric is None or threshold is None:
            return None
        actual = ctx.get(f"quality_{metric}")
        if actual is None:
            return None
        action = rules.get("action_on_breach", "warn")
        # For metrics like null_rate, exceeding threshold is bad
        if metric in ("null_rate",):
            if actual > threshold and action == "deny":
                return rules.get("reason", f"Quality gate '{metric}' breached")
        # For metrics like uniqueness / referential_integrity, below threshold is bad
        else:
            if actual < threshold and action == "deny":
                return rules.get("reason", f"Quality gate '{metric}' breached")
        return None

    # handler dispatch table
    _RULE_HANDLERS: dict[str, Any] = {
        "action_allowlist": _check_action_allowlist,
        "environment_restriction": _check_environment_restriction,
        "data_access": _check_data_access,
        "data_classification": _check_data_classification,
        "data_export": _check_data_export,
        "rate_limit": _check_rate_limit,
        "quality_gate": _check_quality_gate,
    }
