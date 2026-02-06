from __future__ import annotations

import io

import edge_tts
import miniaudio


class TTSSynthesizer:
    """Text-to-speech using edge-tts (Microsoft Edge online TTS)."""

    def __init__(
        self,
        voice: str = "en-US-GuyNeural",
        rate: str = "+0%",
        volume: str = "+0%",
    ):
        self.voice = voice
        self.rate = rate
        self.volume = volume

    async def synthesize(self, text: str) -> bytes:
        """Convert text to raw PCM int16 audio bytes at 24kHz."""
        communicate = edge_tts.Communicate(
            text, self.voice, rate=self.rate, volume=self.volume
        )

        audio_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])

        audio_buffer.seek(0)
        return self._mp3_to_pcm(audio_buffer.read())

    def _mp3_to_pcm(self, mp3_data: bytes) -> bytes:
        """Decode MP3 to raw PCM int16 at 24kHz mono."""
        decoded = miniaudio.decode(
            mp3_data,
            sample_rate=24000,
            nchannels=1,
            output_format=miniaudio.SampleFormat.SIGNED16,
        )
        return bytes(decoded.samples)
