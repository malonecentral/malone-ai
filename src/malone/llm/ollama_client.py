from __future__ import annotations

import json

from openai import AsyncOpenAI

from malone.llm.base import LLMClient, LLMResponse, ToolCall


class OllamaClient(LLMClient):
    """Client for Ollama via OpenAI-compatible API."""

    def __init__(self, config):
        self.model = config.model
        self.timeout = config.timeout
        self.client = AsyncOpenAI(
            base_url=config.base_url,
            api_key="ollama",  # Ollama doesn't require a real key
            timeout=config.timeout,
        )

    async def chat(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> LLMResponse:
        kwargs: dict = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        response = await self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        message = choice.message

        tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                args = tc.function.arguments
                if isinstance(args, str):
                    args = json.loads(args)
                tool_calls.append(
                    ToolCall(id=tc.id, name=tc.function.name, arguments=args)
                )

        return LLMResponse(
            content=message.content or "",
            tool_calls=tool_calls,
        )
