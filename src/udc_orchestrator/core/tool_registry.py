"""UDC Orchestrator — Tool registry for Copilot-callable UDC subsystem tools.

Maintains a catalog of all UDC subsystem tools that can be invoked by the
Copilot SDK during chat interactions and workflow execution.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

import structlog

logger = structlog.get_logger(__name__)

ToolHandler = Callable[..., Coroutine[Any, Any, dict[str, Any]]]


@dataclass
class ToolDef:
    """Definition of a registered Copilot tool."""

    name: str
    description: str
    schema: dict[str, Any]
    handler: ToolHandler
    metadata: dict[str, Any] = field(default_factory=dict)


# Default tool registrations mapping UDC subsystems to Copilot tools
DEFAULT_TOOLS = [
    {
        "name": "classify_data",
        "description": "Classify data assets using the UDC Classifier engine (PII, sensitivity, domain tagging)",
        "subsystem": "Classifier",
    },
    {
        "name": "search_metadata",
        "description": "Search and retrieve metadata from the UDC MetaCatalog",
        "subsystem": "MetaCatalog",
    },
    {
        "name": "store_context",
        "description": "Store and retrieve organizational context via ContextVault",
        "subsystem": "ContextVault",
    },
    {
        "name": "parse_screen",
        "description": "Parse and extract structured data from screen captures via VisionLens",
        "subsystem": "VisionLens",
    },
    {
        "name": "execute_desktop",
        "description": "Execute desktop automation actions via DesktopAgent",
        "subsystem": "DesktopAgent",
    },
    {
        "name": "check_policy",
        "description": "Validate data operations against governance policies via PolicyGuard",
        "subsystem": "PolicyGuard",
    },
]


class ToolRegistry:
    """Registry of UDC subsystem tools available to the Copilot SDK.

    Each tool maps to a UDC subsystem endpoint:
    - classify_data   → Classifier
    - search_metadata → MetaCatalog
    - store_context   → ContextVault
    - parse_screen    → VisionLens
    - execute_desktop → DesktopAgent
    - check_policy    → PolicyGuard
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDef] = {}

    def register(
        self,
        name: str,
        description: str,
        schema: dict[str, Any],
        handler: ToolHandler,
    ) -> None:
        """Register a tool with the given name, schema, and handler.

        Args:
            name: Unique tool identifier.
            description: Human-readable description for Copilot tool discovery.
            schema: JSON Schema for the tool's input parameters.
            handler: Async callable that executes the tool logic.
        """
        logger.info("tool_registry.register", tool_name=name)
        self._tools[name] = ToolDef(
            name=name,
            description=description,
            schema=schema,
            handler=handler,
        )

    def get(self, name: str) -> ToolDef:
        """Retrieve a registered tool by name.

        Args:
            name: The tool identifier.

        Returns:
            The ToolDef for the requested tool.

        Raises:
            KeyError: If the tool is not registered.
        """
        logger.info("tool_registry.get", tool_name=name)
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered")
        return self._tools[name]

    def list_all(self) -> list[ToolDef]:
        """List all registered tools.

        Returns:
            List of all ToolDef entries in the registry.
        """
        logger.info("tool_registry.list_all", count=len(self._tools))
        return list(self._tools.values())

    async def invoke(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Invoke a registered tool by name with the given arguments.

        Args:
            name: The registered tool name.
            args: Arguments matching the tool's input schema.

        Returns:
            Tool execution result as a dictionary.
        """
        tool = self.get(name)
        logger.info("tool_registry.invoke", tool_name=name)
        try:
            result = await tool.handler(**args)
            return {"status": "success", "tool": name, "result": result}
        except Exception as exc:
            logger.error("tool_registry.invoke_error", tool_name=name, error=str(exc))
            return {"status": "error", "tool": name, "error": str(exc)}
