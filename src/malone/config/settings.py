from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import SecretStr
from pydantic_settings import BaseSettings


class AudioSettings(BaseSettings):
    sample_rate: int = 16000
    channels: int = 1
    blocksize: int = 480  # 30ms at 16kHz
    input_device: int | None = None
    output_device: int | None = None


class VADSettings(BaseSettings):
    threshold: float = 0.5
    silence_threshold: float = 0.8  # seconds of silence to end utterance
    min_speech_duration: float = 0.3


class STTSettings(BaseSettings):
    model_size: str = "base.en"
    device: str = "cpu"
    compute_type: str = "int8"


class TTSSettings(BaseSettings):
    voice: str = "en-US-GuyNeural"
    rate: str = "+0%"
    volume: str = "+0%"


class OllamaSettings(BaseSettings):
    base_url: str = "http://mck8s.malonecentral.com:30021/v1"
    model: str = "llama3.1:8b"
    timeout: float = 30.0


class ClaudeSettings(BaseSettings):
    api_key: SecretStr = SecretStr("")
    model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 1024


class HomeAssistantSettings(BaseSettings):
    url: str = ""
    token: SecretStr = SecretStr("")


class MaloneSettings(BaseSettings):
    model_config = {"env_prefix": "MALONE_", "env_nested_delimiter": "__"}

    audio: AudioSettings = AudioSettings()
    vad: VADSettings = VADSettings()
    stt: STTSettings = STTSettings()
    tts: TTSSettings = TTSSettings()
    ollama: OllamaSettings = OllamaSettings()
    claude: ClaudeSettings = ClaudeSettings()
    home_assistant: HomeAssistantSettings = HomeAssistantSettings()

    system_prompt: str = (
        "You are Malone, a helpful personal AI assistant for Dennis. "
        "You control smart home devices, manage network infrastructure, "
        "and help with daily tasks. Keep voice responses concise."
    )


def _load_yaml_config() -> dict:
    """Load config.yaml if it exists."""
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


@lru_cache
def get_settings() -> MaloneSettings:
    """Load settings from environment variables and config.yaml."""
    yaml_config = _load_yaml_config()
    return MaloneSettings(**yaml_config)
