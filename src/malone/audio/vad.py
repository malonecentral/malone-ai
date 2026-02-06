from __future__ import annotations

import numpy as np
import torch


class VoiceActivityDetector:
    """Wraps Silero VAD for speech detection on audio chunks."""

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.model, _ = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            trust_repo=True,
        )
        self.model.eval()

    def is_speech(self, audio_chunk: bytes, sample_rate: int = 16000) -> bool:
        """Check if an audio chunk contains speech."""
        audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
        audio_float = audio_array.astype(np.float32) / 32768.0
        tensor = torch.from_numpy(audio_float)
        confidence = self.model(tensor, sample_rate).item()
        return confidence >= self.threshold

    def reset(self):
        """Reset internal VAD state between utterances."""
        self.model.reset_states()
