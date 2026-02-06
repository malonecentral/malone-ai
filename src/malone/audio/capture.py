from __future__ import annotations

import os
import subprocess
import threading


class AudioCapture:
    """Captures microphone audio using PulseAudio's parec (reliable on WSL2)."""

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
        self._process: subprocess.Popen | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    def start(self, callback):
        """Start capturing audio. callback receives (indata, frames, time, status)."""
        env = os.environ.copy()
        env["PULSE_SERVER"] = "unix:/mnt/wslg/PulseServer"

        self._process = subprocess.Popen(
            [
                "parec",
                "--format=s16le",
                f"--rate={self.sample_rate}",
                f"--channels={self.channels}",
                "--raw",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=env,
        )
        self._running = True

        bytes_per_chunk = self.blocksize * self.channels * 2  # int16 = 2 bytes

        def _reader():
            import numpy as np

            while self._running and self._process and self._process.poll() is None:
                data = self._process.stdout.read(bytes_per_chunk)
                if not data:
                    break
                indata = np.frombuffer(data, dtype="int16").reshape(-1, self.channels)
                callback(indata, len(indata), None, None)

        self._thread = threading.Thread(target=_reader, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._process:
            self._process.terminate()
            self._process.wait()
            self._process = None
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
