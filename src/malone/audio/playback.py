from __future__ import annotations

import asyncio
import os
import subprocess


class AudioPlayback:
    """Plays audio through PulseAudio's paplay (reliable on WSL2)."""

    def __init__(self, sample_rate: int = 24000, device: int | None = None):
        self.sample_rate = sample_rate
        self.device = device

    async def play(self, audio_data: bytes):
        """Play raw PCM int16 audio data asynchronously."""
        env = os.environ.copy()
        env["PULSE_SERVER"] = "unix:/mnt/wslg/PulseServer"

        process = await asyncio.create_subprocess_exec(
            "paplay",
            "--raw",
            "--format=s16le",
            f"--rate={self.sample_rate}",
            "--channels=1",
            stdin=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            env=env,
        )
        await process.communicate(input=audio_data)
