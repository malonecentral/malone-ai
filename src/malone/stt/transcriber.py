from __future__ import annotations

import numpy as np
from faster_whisper import WhisperModel


class Transcriber:
    """Speech-to-text using faster-whisper."""

    def __init__(
        self,
        model_size: str = "base.en",
        device: str = "cpu",
        compute_type: str = "int8",
    ):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_data: bytes) -> str:
        """Transcribe raw PCM int16 audio at 16kHz to text."""
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        audio_float = audio_array.astype(np.float32) / 32768.0

        segments, _ = self.model.transcribe(audio_float, beam_size=5)
        text = " ".join(segment.text.strip() for segment in segments)
        return text.strip()
