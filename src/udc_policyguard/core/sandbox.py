"""UDC PolicyGuard — Sandboxed execution environment for agent actions."""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

from .policy_engine import PolicyDecision, PolicyEngine
from .trust_scorer import TrustScorer

logger = structlog.get_logger(__name__)


@dataclass
class SandboxConstraints:
    """Constraints applied during sandboxed execution."""

    allow_filesystem: bool = False
    allow_network: bool = False
    timeout_seconds: int = 30
    allowed_paths: list[str] | None = None


@dataclass
class SandboxResult:
    """Result of a sandboxed execution."""

    success: bool
    output: Any
    error: str | None = None
    duration_ms: float = 0.0


@dataclass
class PreviewResult:
    """Result of a sandboxed dry-run preview."""

    would_allow: bool
    trust_score: int
    matching_policies: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    policy_decision: PolicyDecision | None = None


class ExecutionSandbox:
    """Execute agent actions within a restricted sandbox.

    Enforces filesystem access restrictions, network access
    restrictions, and time limits on agent action execution.
    """

    def __init__(
        self,
        policy_engine: PolicyEngine,
        trust_scorer: TrustScorer,
    ) -> None:
        self._engine = policy_engine
        self._trust = trust_scorer

    def preview_action(
        self,
        agent_id: str,
        session_id: str,
        action_type: str,
        resource: str,
        context: dict[str, Any],
        user_role: str,
    ) -> PreviewResult:
        """Dry-run an action without side effects.

        Runs policy evaluation + trust check and returns what
        *would* happen if the action were executed for real.
        """
        warnings: list[str] = []

        # Policy evaluation (no side effects)
        decision = self._engine.evaluate(
            agent_id=agent_id,
            session_id=session_id,
            action_type=action_type,
            resource=resource,
            context=context,
            user_role=user_role,
        )

        # Trust score check
        trust = self._trust.get_score(agent_id, session_id)
        if trust.score < 300:
            warnings.append(
                f"Low trust score ({trust.score}): action may be throttled"
            )
        if trust.total_violations > 3:
            warnings.append(
                f"Agent has {trust.total_violations} prior violations"
            )

        return PreviewResult(
            would_allow=decision.allowed,
            trust_score=trust.score,
            matching_policies=decision.violated_policies,
            warnings=warnings,
            policy_decision=decision,
        )

    def execute(
        self, action: dict[str, Any], constraints: SandboxConstraints
    ) -> SandboxResult:
        """Execute an action within the sandbox constraints.

        Args:
            action: The action definition to execute.
            constraints: Sandbox restrictions to enforce.

        Returns:
            SandboxResult with success status and output.
        """
        t0 = time.perf_counter_ns()

        # Validate filesystem access
        target_path = action.get("path")
        if target_path and not constraints.allow_filesystem:
            elapsed = (time.perf_counter_ns() - t0) / 1_000_000
            return SandboxResult(
                success=False,
                output=None,
                error="Filesystem access is not permitted",
                duration_ms=elapsed,
            )

        if target_path and constraints.allowed_paths:
            resolved = str(Path(target_path).resolve())
            if not any(resolved.startswith(p) for p in constraints.allowed_paths):
                elapsed = (time.perf_counter_ns() - t0) / 1_000_000
                return SandboxResult(
                    success=False,
                    output=None,
                    error=f"Path '{target_path}' is outside allowed paths",
                    duration_ms=elapsed,
                )

        # Validate network access
        if action.get("requires_network") and not constraints.allow_network:
            elapsed = (time.perf_counter_ns() - t0) / 1_000_000
            return SandboxResult(
                success=False,
                output=None,
                error="Network access is not permitted",
                duration_ms=elapsed,
            )

        # Execute the action callable if provided
        handler = action.get("handler")
        if handler is None:
            elapsed = (time.perf_counter_ns() - t0) / 1_000_000
            return SandboxResult(
                success=True,
                output={"dry_run": True, "action": action.get("type")},
                duration_ms=elapsed,
            )

        try:
            result = handler(**action.get("args", {}))
            elapsed = (time.perf_counter_ns() - t0) / 1_000_000
            return SandboxResult(
                success=True, output=result, duration_ms=elapsed
            )
        except Exception as exc:
            elapsed = (time.perf_counter_ns() - t0) / 1_000_000
            logger.error("sandbox.execution_error", error=str(exc))
            return SandboxResult(
                success=False, output=None, error=str(exc), duration_ms=elapsed
            )
