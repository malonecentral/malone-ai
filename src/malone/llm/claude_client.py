from __future__ import annotations

import json

from anthropic import AsyncAnthropic

from malone.llm.base import LLMClient, LLMResponse, ToolCall


class ClaudeClient(LLMClient):
    """Client for Anthropic Claude API."""

    def __init__(self, config):
        self.model = config.model
        self.max_tokens = config.max_tokens
        self.client = AsyncAnthropic(
            api_key=config.api_key.get_secret_value(),
        )

    async def chat(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> LLMResponse:
        # Separate system message from conversation messages
        system_prompt = ""
        conversation = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                conversation.append(self._convert_message(msg))

        kwargs: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": conversation,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        if tools:
            kwargs["tools"] = [self._convert_tool(t) for t in tools]

        response = await self.client.messages.create(**kwargs)

        # Parse response content and tool calls
        content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input,
                    )
                )

        return LLMResponse(content=content, tool_calls=tool_calls)

    def _convert_message(self, msg: dict) -> dict:
        """Convert OpenAI-format message to Anthropic format."""
        role = msg["role"]

        # Tool results → Anthropic tool_result blocks
        if role == "tool":
            return {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": msg["tool_call_id"],
                        "content": msg["content"],
                    }
                ],
            }

        # Assistant messages with tool calls → Anthropic content blocks
        if role == "assistant" and "tool_calls" in msg:
            content_blocks = []
            if msg.get("content"):
                content_blocks.append({"type": "text", "text": msg["content"]})
            for tc in msg["tool_calls"]:
                args = tc["function"]["arguments"]
                if isinstance(args, str):
                    args = json.loads(args)
                content_blocks.append({
                    "type": "tool_use",
                    "id": tc["id"],
                    "name": tc["function"]["name"],
                    "input": args,
                })
            return {"role": "assistant", "content": content_blocks}

        # Plain user/assistant messages
        return {"role": role, "content": msg["content"]}

    def _convert_tool(self, tool: dict) -> dict:
        """Convert OpenAI tool schema to Anthropic format."""
        func = tool["function"]
        return {
            "name": func["name"],
            "description": func["description"],
            "input_schema": func["parameters"],
        }
