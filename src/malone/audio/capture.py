from __future__ import annotations

import sounddevice as sd


class AudioCapture:
    """Captures microphone audio using sounddevice with a callback."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        blocksize: int = 480,
        device: int | None = None,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.blocksize = blocksize
        self.device = device
        self._stream: sd.InputStream | None = None

    def start(self, callback):
        """Start capturing audio. callback receives (indata, frames, time, status)."""
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16",
            blocksize=self.blocksize,
            device=self.device,
            callback=callback,
        )
        self._stream.start()

    def stop(self):
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
