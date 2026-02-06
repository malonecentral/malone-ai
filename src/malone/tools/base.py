from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Base class for all Malone tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool name."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what the tool does (shown to LLM)."""
        ...

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """JSON Schema for the tool parameters."""
        ...

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with the given arguments."""
        ...

    def to_openai_schema(self) -> dict:
        """Return OpenAI-compatible tool schema for LLM function calling."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
