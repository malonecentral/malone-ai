from __future__ import annotations

from malone.llm.base import LLMClient, LLMResponse


# Keywords that suggest a complex query needing Claude
_COMPLEX_KEYWORDS = [
    "analyze", "explain", "refactor", "debug", "review",
    "write code", "implement", "architecture", "design",
    "compare", "summarize", "translate", "improve yourself",
    "edit your code", "add a feature", "complex",
]


class LLMRouter(LLMClient):
    """Routes queries between a fast local LLM and a smart cloud LLM.

    Simple/short queries go to Ollama (fast, free, local).
    Complex/long queries go to Claude (smart, tool-savvy, cloud).
    Falls back to the other if one fails.
    """

    def __init__(
        self,
        local: LLMClient,
        cloud: LLMClient | None = None,
        complexity_threshold: int = 500,
    ):
        self.local = local
        self.cloud = cloud
        self.complexity_threshold = complexity_threshold

    async def chat(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> LLMResponse:
        use_cloud = self.cloud is not None and self._should_use_cloud(messages)

        if use_cloud:
            try:
                print("  [Router: using Claude]")
                return await self.cloud.chat(messages, tools=tools)
            except Exception as e:
                print(f"  [Router: Claude failed ({e}), falling back to Ollama]")
                return await self.local.chat(messages, tools=tools)
        else:
            try:
                print("  [Router: using Ollama]")
                return await self.local.chat(messages, tools=tools)
            except Exception as e:
                if self.cloud:
                    print(f"  [Router: Ollama failed ({e}), falling back to Claude]")
                    return await self.cloud.chat(messages, tools=tools)
                raise

    def _should_use_cloud(self, messages: list[dict]) -> bool:
        """Decide whether to route to cloud LLM."""
        # Get the last user message
        last_user = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user = msg.get("content", "")
                break

        if not last_user:
            return False

        # Long messages suggest complexity
        if len(last_user) > self.complexity_threshold:
            return True

        # Check for complexity keywords
        lower = last_user.lower()
        for keyword in _COMPLEX_KEYWORDS:
            if keyword in lower:
                return True

        return False
