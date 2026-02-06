from __future__ import annotations

import os

from malone.audio.capture import AudioCapture
from malone.audio.playback import AudioPlayback
from malone.audio.vad import VoiceActivityDetector
from malone.config.settings import get_settings
from malone.conversation.loop import ConversationLoop
from malone.conversation.manager import ConversationManager
from malone.llm.ollama_client import OllamaClient
from malone.llm.router import LLMRouter
from malone.stt.transcriber import Transcriber
from malone.tools.executor import ToolExecutor
from malone.tools.registry import ToolRegistry
from malone.tts.synthesizer import TTSSynthesizer


class MaloneApp:
    """Main application - wires all components together."""

    def __init__(self):
        self.settings = get_settings()

    async def run(self):
        # Ensure PulseAudio is configured for WSL2
        os.environ.setdefault("PULSE_SERVER", "unix:/mnt/wslg/PulseServer")

        print("Malone AI starting up...")
        print()

        # Initialize components
        print("  Loading voice activity detection...")
        vad = VoiceActivityDetector(threshold=self.settings.vad.threshold)

        print("  Loading speech recognition...")
        transcriber = Transcriber(
            model_size=self.settings.stt.model_size,
            device=self.settings.stt.device,
            compute_type=self.settings.stt.compute_type,
        )

        print("  Connecting to Ollama...")
        ollama = OllamaClient(self.settings.ollama)

        # Set up Claude as cloud fallback if API key is configured
        cloud_llm = None
        claude_key = self.settings.claude.api_key.get_secret_value()
        if claude_key:
            from malone.llm.claude_client import ClaudeClient
            print("  Connecting to Claude API (cloud fallback)...")
            cloud_llm = ClaudeClient(self.settings.claude)

        llm = LLMRouter(local=ollama, cloud=cloud_llm)

        # Initialize tool system
        print("  Loading tools...")
        registry = ToolRegistry()
        registry.auto_discover()
        tool_executor = ToolExecutor(registry)
        print(f"    Registered tools: {registry.list_tools()}")

        audio_capture = AudioCapture(
            sample_rate=self.settings.audio.sample_rate,
            channels=self.settings.audio.channels,
            blocksize=self.settings.audio.blocksize,
            device=self.settings.audio.input_device,
        )

        audio_playback = AudioPlayback(
            sample_rate=tts.sample_rate,  # Match TTS output rate
            device=self.settings.audio.output_device,
        )

        print("  Loading text-to-speech (Piper)...")
        tts = TTSSynthesizer(
            voice=self.settings.tts.voice,
        )

        conversation = ConversationManager(
            system_prompt=self.settings.system_prompt,
        )

        loop = ConversationLoop(
            audio_capture=audio_capture,
            audio_playback=audio_playback,
            vad=vad,
            transcriber=transcriber,
            llm=llm,
            tts=tts,
            conversation=conversation,
            tool_executor=tool_executor,
            silence_threshold=self.settings.vad.silence_threshold,
            min_speech_duration=self.settings.vad.min_speech_duration,
        )

        print()
        print("Malone is ready. Start speaking!")
        print("Press Ctrl+C to exit.")
        print()

        await loop.run()
