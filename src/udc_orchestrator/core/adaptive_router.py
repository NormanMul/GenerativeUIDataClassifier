"""UDC Orchestrator — Adaptive role-based request routing.

Routes user requests to the appropriate agent configuration based on the
user's role, providing tailored interaction modes for different personas.
"""

from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class AgentConfig:
    """Configuration for a role-specific agent mode."""

    mode: str
    description: str
    system_prompt: str
    available_tools: list[str] = field(default_factory=list)
    model_preference: str = "gpt-4o"
    temperature: float = 0.3
    max_tokens: int = 4096


@dataclass
class WorkflowSelection:
    """Result of routing a user request to a workflow."""

    workflow_name: str
    confidence: float
    parameters: dict[str, Any] = field(default_factory=dict)
    agent_config: AgentConfig | None = None


# Role-based agent configurations
ROLE_CONFIGS: dict[str, AgentConfig] = {
    "business_analyst": AgentConfig(
        mode="guided_wizard",
        description="Guided wizard mode with step-by-step data exploration",
        system_prompt=(
            "You are a data discovery assistant helping a business analyst. "
            "Guide them step-by-step through data exploration, classification, "
            "and documentation. Use plain language, avoid technical jargon, "
            "and suggest next actions proactively."
        ),
        available_tools=[
            "search_metadata",
            "classify_data",
            "store_context",
            "parse_screen",
        ],
        model_preference="gpt-4o",
        temperature=0.4,
    ),
    "data_engineer": AgentConfig(
        mode="technical_deep",
        description="Technical deep mode with full tool access and detailed output",
        system_prompt=(
            "You are a technical data engineering assistant. Provide detailed "
            "technical information, SQL snippets, lineage graphs, and profiling "
            "statistics. Support pipeline debugging and schema analysis."
        ),
        available_tools=[
            "classify_data",
            "search_metadata",
            "store_context",
            "parse_screen",
            "execute_desktop",
            "check_policy",
        ],
        model_preference="gpt-4o",
        temperature=0.2,
    ),
    "data_steward": AgentConfig(
        mode="governance_first",
        description="Governance-first mode prioritizing policy compliance and quality",
        system_prompt=(
            "You are a data governance assistant. Prioritize policy compliance, "
            "data quality validation, and classification accuracy. Flag potential "
            "policy violations, suggest remediation steps, and enforce governance "
            "standards in every recommendation."
        ),
        available_tools=[
            "check_policy",
            "classify_data",
            "search_metadata",
            "store_context",
        ],
        model_preference="gpt-4o",
        temperature=0.2,
    ),
}

# Keyword → workflow mapping for simple intent classification
_INTENT_KEYWORDS: dict[str, list[str]] = {
    "data_classification": [
        "classify", "classification", "pii", "sensitivity", "tag", "label",
        "detect", "scan",
    ],
    "quality_audit": [
        "quality", "audit", "null", "uniqueness", "integrity", "validate",
        "profil",
    ],
    "pipeline_documentation": [
        "document", "lineage", "pipeline", "catalog", "glossary",
    ],
    "dashboard_builder": [
        "dashboard", "report", "chart", "visualiz", "metric",
    ],
}

DEFAULT_WORKFLOW = "data_classification"


class AdaptiveRouter:
    """Routes requests to role-appropriate agent configurations.

    Maps user roles to tailored agent modes:
    - Business Analyst → Guided wizard mode (step-by-step, plain language)
    - Data Engineer    → Technical deep mode (full access, detailed output)
    - Data Steward     → Governance-first mode (policy compliance priority)
    """

    def __init__(self) -> None:
        self._configs = dict(ROLE_CONFIGS)

    async def route(
        self, user_role: str, request: dict[str, Any]
    ) -> AgentConfig:
        """Determine the agent configuration for the given user role and request.

        Args:
            user_role: The authenticated user's role (e.g. 'business_analyst').
            request: The incoming request context for further routing decisions.

        Returns:
            AgentConfig tailored to the user's role and request context.
        """
        logger.info(
            "adaptive_router.route",
            user_role=user_role,
            request_keys=list(request.keys()),
        )

        config = self._configs.get(user_role)
        if config is None:
            logger.warning(
                "adaptive_router.unknown_role",
                user_role=user_role,
                fallback="data_engineer",
            )
            config = self._configs["data_engineer"]

        return config

    async def select_workflow(
        self, user_role: str, message: str
    ) -> WorkflowSelection:
        """Classify user intent and select the best workflow.

        Uses simple keyword matching for deterministic cases and
        falls back to a default workflow when ambiguous.

        Args:
            user_role: The authenticated user's role.
            message: The user's natural language message.

        Returns:
            WorkflowSelection with chosen workflow and confidence.
        """
        msg_lower = message.lower()
        scores: dict[str, int] = {}

        for workflow, keywords in _INTENT_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw in msg_lower)
            if hits:
                scores[workflow] = hits

        agent_config = await self.route(user_role, {"message": message})

        if scores:
            best = max(scores, key=scores.__getitem__)
            confidence = min(1.0, scores[best] / 3.0)
            logger.info(
                "adaptive_router.workflow_selected",
                workflow=best,
                confidence=confidence,
                scores=scores,
            )
            return WorkflowSelection(
                workflow_name=best,
                confidence=confidence,
                parameters={"user_message": message, "user_role": user_role},
                agent_config=agent_config,
            )

        logger.info("adaptive_router.default_workflow", workflow=DEFAULT_WORKFLOW)
        return WorkflowSelection(
            workflow_name=DEFAULT_WORKFLOW,
            confidence=0.3,
            parameters={"user_message": message, "user_role": user_role},
            agent_config=agent_config,
        )
