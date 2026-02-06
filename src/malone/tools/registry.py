from __future__ import annotations

import importlib
import pkgutil
from typing import Any

from malone.tools.base import BaseTool


class ToolRegistry:
    """Discovers, registers, and manages available tools."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def get_all_schemas(self) -> list[dict]:
        """Return OpenAI-compatible tool schemas for LLM."""
        return [tool.to_openai_schema() for tool in self._tools.values()]

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def auto_discover(self, package_path: str = "malone.tools.builtin"):
        """Automatically discover and register tool classes from a package."""
        package = importlib.import_module(package_path)
        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            module = importlib.import_module(f"{package_path}.{module_name}")
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseTool)
                    and attr is not BaseTool
                ):
                    try:
                        self.register(attr())
                    except Exception as e:
                        print(f"  [Warning: Failed to register {attr_name}: {e}]")
