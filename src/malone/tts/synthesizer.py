from __future__ import annotations

import asyncio

import numpy as np
from piper import PiperVoice

VOICE_DIR = "/home/dennis/.local/share/piper-voices"


class TTSSynthesizer:
    """Text-to-speech using Piper TTS (local, fast, offline)."""

    def __init__(
        self,
        voice: str = "en_GB-alba-medium",
        rate: str = "+0%",
        volume: str = "+0%",
    ):
        model_path = f"{VOICE_DIR}/{voice}.onnx"
        self._voice = PiperVoice.load(model_path)
        self.sample_rate = self._voice.config.sample_rate

    async def synthesize(self, text: str) -> bytes:
        """Convert text to raw PCM int16 audio bytes."""
        return await asyncio.to_thread(self._synthesize_sync, text)

    def _synthesize_sync(self, text: str) -> bytes:
        """Synchronous synthesis (Piper is CPU-bound)."""
        audio_chunks = []
        for chunk in self._voice.synthesize(text):
            int_audio = (chunk.audio_float_array * 32767).astype(np.int16)
            audio_chunks.append(int_audio.tobytes())
        return b"".join(audio_chunks)
