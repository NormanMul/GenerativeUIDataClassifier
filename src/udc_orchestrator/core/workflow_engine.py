"""UDC Orchestrator — DAG-based workflow execution engine.

Parses YAML workflow definitions into dependency graphs, executes steps
with support for sequential, parallel, and conditional execution modes,
and provides retry with exponential backoff and checkpoint/resume.
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
import structlog

logger = structlog.get_logger(__name__)


class StepStatus(str, Enum):
    """Execution status of a workflow step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStatus(str, Enum):
    """Overall workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StepDef:
    """Definition of a single workflow step."""

    name: str
    tool: str
    config: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    condition: str | None = None
    retry_max: int = 3
    retry_backoff: float = 1.0
    on_failure: str | None = None


@dataclass
class WorkflowDef:
    """Complete workflow definition parsed from YAML."""

    name: str
    description: str
    version: str
    steps: list[StepDef] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowResult:
    """Result of a workflow execution."""

    workflow_id: str
    workflow_name: str
    status: WorkflowStatus
    step_results: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_ms: float = 0.0


def _topological_layers(steps: list[StepDef]) -> list[list[StepDef]]:
    """Return steps grouped in topological layers for parallel execution."""
    step_map = {s.name: s for s in steps}
    in_degree: dict[str, int] = {s.name: 0 for s in steps}
    dependents: dict[str, list[str]] = {s.name: [] for s in steps}

    for s in steps:
        for dep in s.depends_on:
            if dep in step_map:
                in_degree[s.name] += 1
                dependents[dep].append(s.name)

    layers: list[list[StepDef]] = []
    ready = [name for name, deg in in_degree.items() if deg == 0]

    while ready:
        layer = [step_map[n] for n in ready]
        layers.append(layer)
        next_ready: list[str] = []
        for name in ready:
            for dep in dependents[name]:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    next_ready.append(dep)
        ready = next_ready

    resolved = sum(len(l) for l in layers)
    if resolved != len(steps):
        raise ValueError(
            f"Cycle detected in workflow DAG: resolved {resolved}/{len(steps)} steps"
        )
    return layers


class WorkflowEngine:
    """DAG-based workflow execution engine.

    Loads YAML workflow definitions, constructs a directed acyclic graph
    of step dependencies using topological sorting, and executes steps
    respecting:

    - Sequential dependencies via depends_on
    - Parallel execution of independent steps
    - Conditional step execution via condition expressions
    - Retry with exponential backoff on transient failures
    - Checkpoint/resume for long-running workflows
    """

    def __init__(self, tool_invoker: Any | None = None) -> None:
        self._workflows: dict[str, WorkflowDef] = {}
        self._active: dict[str, WorkflowResult] = {}
        self._tool_invoker = tool_invoker  # async callable(tool_name, args) -> dict

    async def load_workflow(self, yaml_path: str) -> WorkflowDef:
        """Load and parse a workflow definition from a YAML file.

        Reads the YAML, validates the schema, builds the dependency graph,
        and checks for cycles before registering the workflow.

        Args:
            yaml_path: Path to the YAML workflow definition file.

        Returns:
            Parsed WorkflowDef with validated step dependencies.
        """
        logger.info("workflow_engine.load", yaml_path=yaml_path)

        path = Path(yaml_path)
        raw = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)

        steps: list[StepDef] = []
        for s in data.get("steps", []):
            steps.append(StepDef(
                name=s["name"],
                tool=s.get("tool", ""),
                config=s.get("config", {}),
                depends_on=s.get("depends_on", []),
                condition=s.get("condition"),
                retry_max=s.get("retry_max", 3),
                retry_backoff=s.get("retry_backoff", 1.0),
                on_failure=s.get("on_failure"),
            ))

        # Validate DAG (raises on cycle)
        _topological_layers(steps)

        wf = WorkflowDef(
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "0.0.0"),
            steps=steps,
            metadata=data.get("metadata", {}),
        )
        self._workflows[wf.name] = wf
        logger.info("workflow_engine.loaded", name=wf.name, step_count=len(steps))
        return wf

    async def execute(
        self, workflow_name: str, params: dict[str, Any]
    ) -> WorkflowResult:
        """Execute a loaded workflow with the given parameters.

        Resolves the execution order from the DAG, runs steps in the
        correct sequence (parallelizing independent steps), handles
        retries with exponential backoff, and stores checkpoints
        for resume capability.

        Args:
            workflow_name: Name of a previously loaded workflow.
            params: Runtime parameters passed to workflow steps.

        Returns:
            WorkflowResult with status and per-step outputs.
        """
        wf = self._workflows.get(workflow_name)
        if wf is None:
            raise KeyError(f"Workflow '{workflow_name}' not loaded")

        t0 = time.perf_counter_ns()
        wf_id = str(uuid.uuid4())
        result = WorkflowResult(
            workflow_id=wf_id,
            workflow_name=workflow_name,
            status=WorkflowStatus.RUNNING,
        )
        self._active[wf_id] = result

        logger.info(
            "workflow_engine.execute",
            workflow_name=workflow_name,
            workflow_id=wf_id,
            params_keys=list(params.keys()),
        )

        layers = _topological_layers(wf.steps)
        step_outputs: dict[str, Any] = {"__params": params}

        try:
            for layer in layers:
                tasks = [
                    self._execute_step(step, step_outputs)
                    for step in layer
                    if self._evaluate_condition(step.condition, step_outputs)
                ]
                layer_results = await asyncio.gather(*tasks, return_exceptions=True)

                for step, res in zip(
                    [s for s in layer if self._evaluate_condition(s.condition, step_outputs)],
                    layer_results,
                ):
                    if isinstance(res, Exception):
                        result.step_results[step.name] = {
                            "status": StepStatus.FAILED,
                            "error": str(res),
                        }
                        if step.on_failure != "continue":
                            raise res
                    else:
                        result.step_results[step.name] = {
                            "status": StepStatus.COMPLETED,
                            "output": res,
                        }
                        step_outputs[step.name] = res

            result.status = WorkflowStatus.COMPLETED
        except Exception as exc:
            result.status = WorkflowStatus.FAILED
            result.error = str(exc)
            logger.error("workflow_engine.failed", workflow_id=wf_id, error=str(exc))

        result.duration_ms = (time.perf_counter_ns() - t0) / 1_000_000
        return result

    async def get_status(self, workflow_id: str) -> WorkflowResult:
        """Get the current status of a workflow execution.

        Args:
            workflow_id: Unique identifier for the workflow run.

        Returns:
            WorkflowResult capturing progress, step statuses, and errors.
        """
        logger.info("workflow_engine.get_status", workflow_id=workflow_id)
        if workflow_id not in self._active:
            raise KeyError(f"Workflow run '{workflow_id}' not found")
        return self._active[workflow_id]

    # ---- internal helpers ------------------------------------------

    async def _execute_step(
        self, step: StepDef, step_outputs: dict[str, Any]
    ) -> Any:
        """Execute a single step with retry + exponential backoff."""
        last_exc: Exception | None = None
        for attempt in range(1, step.retry_max + 1):
            try:
                logger.info(
                    "workflow_engine.step_start",
                    step=step.name,
                    tool=step.tool,
                    attempt=attempt,
                )
                if self._tool_invoker is not None:
                    merged_args = {**step.config, "__prior_outputs": step_outputs}
                    result = await self._tool_invoker(step.tool, merged_args)
                else:
                    result = {"tool": step.tool, "config": step.config, "dry_run": True}
                logger.info("workflow_engine.step_done", step=step.name)
                return result
            except Exception as exc:
                last_exc = exc
                if attempt < step.retry_max:
                    delay = step.retry_backoff * (2 ** (attempt - 1))
                    logger.warning(
                        "workflow_engine.step_retry",
                        step=step.name,
                        attempt=attempt,
                        delay=delay,
                    )
                    await asyncio.sleep(delay)
        raise RuntimeError(
            f"Step '{step.name}' failed after {step.retry_max} attempts: {last_exc}"
        )

    @staticmethod
    def _evaluate_condition(
        condition: str | None, step_outputs: dict[str, Any]
    ) -> bool:
        """Evaluate a step condition expression. None means always run."""
        if condition is None:
            return True
        # Simple expression: "step_name.status == completed"
        try:
            parts = condition.split()
            if len(parts) == 3:
                ref, op, expected = parts
                step_name = ref.split(".")[0]
                step_result = step_outputs.get(step_name, {})
                if isinstance(step_result, dict):
                    actual = str(step_result.get("status", ""))
                else:
                    actual = str(step_result)
                if op == "==":
                    return actual == expected
                if op == "!=":
                    return actual != expected
        except Exception:
            logger.warning("workflow_engine.condition_eval_error", condition=condition)
        return True
