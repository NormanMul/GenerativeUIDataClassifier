"""UDC Orchestrator — Copilot SDK bridge for AI-powered tool orchestration.

Integrates with GitHub Copilot SDK via JSON-RPC protocol to provide
multi-model routing (GPT-4o, Claude, Gemini) and tool execution capabilities.
"""

import json
from typing import Any, AsyncIterator

import httpx
import structlog

logger = structlog.get_logger(__name__)


class CopilotBridge:
    """Bridge between UDC Orchestrator and GitHub Copilot SDK.

    Manages the lifecycle of Copilot SDK connections, registers UDC tools
    as Copilot-callable functions, and routes requests across multiple
    LLM backends (GPT-4o, Claude, Gemini) based on task characteristics.

    Communication uses JSON-RPC over stdio/HTTP, matching the Copilot
    extension protocol for tool definitions and invocation.
    """

    def __init__(self) -> None:
        self._tools: dict[str, dict[str, Any]] = {}
        self._config: dict[str, Any] = {}
        self._initialized: bool = False
        self._http: httpx.AsyncClient | None = None

    async def initialize(self, config: dict[str, Any]) -> None:
        """Initialize the Copilot SDK connection and configure model routing.

        Args:
            config: Configuration dict with keys for endpoint URLs,
                    API keys, model preferences, and routing rules.
        """
        logger.info("copilot_bridge.initialize", config_keys=list(config.keys()))
        self._config = config
        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            headers={
                "Content-Type": "application/json",
                "api-key": config.get("api_key", ""),
            },
        )
        self._initialized = True
        logger.info("copilot_bridge.initialized")

    async def register_tool(
        self,
        name: str,
        schema: dict[str, Any],
        handler: Any,
    ) -> None:
        """Register a UDC tool so Copilot can discover and invoke it.

        Args:
            name: Unique tool identifier (e.g. 'classify_data').
            schema: JSON Schema describing the tool's parameters and return type.
            handler: Async callable that executes the tool logic.
        """
        logger.info("copilot_bridge.register_tool", tool_name=name)
        self._tools[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": schema.get("description", ""),
                "parameters": schema,
            },
            "_handler": handler,
        }

    async def execute_tool(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Execute a registered tool by name with the given arguments.

        Args:
            name: The registered tool name.
            args: Arguments matching the tool's input schema.

        Returns:
            Tool execution result as a dictionary.
        """
        logger.info("copilot_bridge.execute_tool", tool_name=name, args_keys=list(args.keys()))
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' is not registered")
        handler = tool["_handler"]
        try:
            result = await handler(**args)
            return {"status": "success", "tool": name, "result": result}
        except Exception as exc:
            logger.error("copilot_bridge.tool_error", tool_name=name, error=str(exc))
            return {"status": "error", "tool": name, "error": str(exc)}

    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[str] | None = None,
    ) -> dict[str, Any]:
        """Send a chat completion request through the Copilot SDK.

        Routes to the optimal model backend (GPT-4o for complex reasoning,
        Claude for long-context analysis, Gemini for multimodal tasks)
        based on message content and available tools.

        Args:
            messages: Conversation history in OpenAI-compatible format.
            tools: Optional list of tool names to make available for this request.

        Returns:
            Chat completion response with optional tool calls.
        """
        logger.info(
            "copilot_bridge.chat",
            message_count=len(messages),
            tools=tools,
        )
        if not self._initialized or self._http is None:
            raise RuntimeError("CopilotBridge not initialized — call initialize() first")

        model = self._select_model(messages)
        endpoint = self._config.get(
            "endpoint",
            self._config.get("azure_openai_endpoint", ""),
        )
        api_version = self._config.get("api_version", "2024-02-15-preview")
        deployment = self._config.get("deployment", model)
        url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"

        # Build the request body
        body: dict[str, Any] = {
            "messages": messages,
            "temperature": self._config.get("temperature", 0.3),
            "max_tokens": self._config.get("max_tokens", 4096),
        }

        # Attach tool definitions if requested
        if tools:
            tool_defs = [
                self._tools[t] for t in tools
                if t in self._tools
            ]
            # Strip internal handler before sending
            body["tools"] = [
                {k: v for k, v in td.items() if k != "_handler"}
                for td in tool_defs
            ]

        resp = await self._http.post(url, json=body)
        resp.raise_for_status()
        data = resp.json()

        # Handle tool_calls in the response
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        tool_calls = message.get("tool_calls", [])

        if tool_calls:
            tool_results = []
            for tc in tool_calls:
                fn = tc.get("function", {})
                tc_name = fn.get("name", "")
                tc_args = json.loads(fn.get("arguments", "{}"))
                result = await self.execute_tool(tc_name, tc_args)
                tool_results.append({
                    "tool_call_id": tc.get("id"),
                    "role": "tool",
                    "content": json.dumps(result, default=str),
                })
            data["tool_results"] = tool_results

        return data

    async def send_message(
        self,
        message: str,
        *,
        role: str = "user",
        tools: list[str] | None = None,
    ) -> AsyncIterator[str]:
        """Send a chat message and yield streaming response chunks via SSE."""
        if not self._initialized or self._http is None:
            raise RuntimeError("CopilotBridge not initialized")

        model = self._select_model([{"role": role, "content": message}])
        endpoint = self._config.get("endpoint", "")
        api_version = self._config.get("api_version", "2024-02-15-preview")
        deployment = self._config.get("deployment", model)
        url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"

        body: dict[str, Any] = {
            "messages": [{"role": role, "content": message}],
            "stream": True,
            "temperature": self._config.get("temperature", 0.3),
        }

        async with self._http.stream("POST", url, json=body) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    chunk = json.loads(line[6:])
                    delta = (
                        chunk.get("choices", [{}])[0]
                        .get("delta", {})
                        .get("content", "")
                    )
                    if delta:
                        yield delta

    # ---- internal helpers ------------------------------------------

    def _select_model(self, messages: list[dict[str, str]]) -> str:
        """Pick the best model based on message characteristics."""
        total_len = sum(len(m.get("content", "")) for m in messages)

        # Long context → prefer Claude; multimodal → Gemini; default → GPT-4o
        if total_len > 30_000:
            return self._config.get("long_context_model", "claude-sonnet")

        has_image = any(
            "image" in m.get("content", "").lower()
            or m.get("type") == "image"
            for m in messages
        )
        if has_image:
            return self._config.get("multimodal_model", "gemini-pro")

        return self._config.get("default_model", "gpt-4o")

    async def close(self) -> None:
        """Gracefully close the HTTP client."""
        if self._http:
            await self._http.aclose()
            self._http = None
            self._initialized = False
