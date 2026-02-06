from __future__ import annotations

import json
import traceback

from malone.tools.registry import ToolRegistry


class ToolExecutor:
    """Executes tool calls from the LLM and returns results."""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    async def execute(self, tool_name: str, arguments: dict) -> str:
        """Execute a tool by name and return the result as a string."""
        tool = self.registry.get(tool_name)
        if tool is None:
            return f"Error: Unknown tool '{tool_name}'. Available: {self.registry.list_tools()}"

        try:
            result = await tool.execute(**arguments)
            return str(result)
        except Exception as e:
            return f"Error executing {tool_name}: {e}\n{traceback.format_exc()}"

    def get_tool_schemas(self) -> list[dict]:
        """Return OpenAI-compatible tool schemas."""
        return self.registry.get_all_schemas()
