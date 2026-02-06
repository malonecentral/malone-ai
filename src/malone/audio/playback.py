from __future__ import annotations

import asyncio

import numpy as np
import sounddevice as sd


class AudioPlayback:
    """Plays audio through the speaker using sounddevice."""

    def __init__(self, sample_rate: int = 24000, device: int | None = None):
        self.sample_rate = sample_rate
        self.device = device

    async def play(self, audio_data: bytes):
        """Play raw PCM int16 audio data asynchronously."""
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._play_sync, audio_array)

    def _play_sync(self, audio_array: np.ndarray):
        sd.play(audio_array, samplerate=self.sample_rate, device=self.device)
        sd.wait()
