from __future__ import annotations


class ConversationManager:
    """Manages conversation message history."""

    def __init__(self, system_prompt: str, max_history: int = 50):
        self.system_prompt = system_prompt
        self.max_history = max_history
        self._messages: list[dict] = []

    def add_user(self, text: str):
        self._messages.append({"role": "user", "content": text})
        self._trim()

    def add_assistant(self, text: str):
        self._messages.append({"role": "assistant", "content": text})
        self._trim()

    def get_messages(self) -> list[dict]:
        """Return full message list including system prompt."""
        return [{"role": "system", "content": self.system_prompt}] + self._messages

    def _trim(self):
        if len(self._messages) > self.max_history:
            self._messages = self._messages[-self.max_history :]
