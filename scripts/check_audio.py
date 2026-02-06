#!/usr/bin/env python3
"""Diagnostic script to verify audio devices work on WSL2."""

import sys


def main():
    print("=== Malone AI - Audio Diagnostic ===\n")

    try:
        import sounddevice as sd
    except ImportError:
        print("ERROR: sounddevice not installed. Run: pip install sounddevice")
        sys.exit(1)

    # List devices
    print("Audio devices found:")
    print(sd.query_devices())
    print()

    # Check default input
    try:
        default_in = sd.query_devices(kind="input")
        print(f"Default INPUT device: {default_in['name']}")
        print(f"  Max input channels: {default_in['max_input_channels']}")
        print(f"  Default sample rate: {default_in['default_samplerate']}")
    except sd.PortAudioError:
        print("WARNING: No default input device found!")
        print("  On WSL2, make sure WSLg is enabled (Windows 11)")
        print("  or configure PulseAudio manually.")

    print()

    # Check default output
    try:
        default_out = sd.query_devices(kind="output")
        print(f"Default OUTPUT device: {default_out['name']}")
        print(f"  Max output channels: {default_out['max_output_channels']}")
        print(f"  Default sample rate: {default_out['default_samplerate']}")
    except sd.PortAudioError:
        print("WARNING: No default output device found!")

    print()

    # Quick recording test
    print("Testing 2-second recording...")
    try:
        import numpy as np

        duration = 2  # seconds
        sample_rate = 16000
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
        )
        sd.wait()
        peak = np.max(np.abs(recording))
        print(f"  Recording complete. Peak amplitude: {peak}")
        if peak < 100:
            print("  WARNING: Very low audio level. Check your microphone.")
        else:
            print("  Microphone is working!")
    except Exception as e:
        print(f"  ERROR during recording: {e}")

    print()

    # Quick playback test
    print("Testing playback (short beep)...")
    try:
        import numpy as np

        sample_rate = 24000
        duration = 0.3
        freq = 440
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        beep = (np.sin(2 * np.pi * freq * t) * 8000).astype(np.int16)
        sd.play(beep, samplerate=sample_rate)
        sd.wait()
        print("  Playback complete. Did you hear a beep?")
    except Exception as e:
        print(f"  ERROR during playback: {e}")

    print("\n=== Diagnostic complete ===")


if __name__ == "__main__":
    main()
