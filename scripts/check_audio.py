#!/usr/bin/env python3
"""Diagnostic script to verify audio devices work on WSL2 via PulseAudio."""

import os
import shutil
import subprocess
import sys
import time


def main():
    print("=== Malone AI - Audio Diagnostic ===\n")

    os.environ.setdefault("PULSE_SERVER", "unix:/mnt/wslg/PulseServer")

    # Check for PulseAudio tools
    for tool in ("paplay", "parec", "pactl"):
        if not shutil.which(tool):
            print(f"ERROR: {tool} not found. Run: sudo apt install pulseaudio-utils")
            sys.exit(1)

    # Check PulseAudio connection
    print("1. PulseAudio connection...")
    try:
        result = subprocess.run(
            ["pactl", "info"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if any(k in line for k in ("Server Name", "Default Sink", "Default Source")):
                    print(f"   {line.strip()}")
            print("   PulseAudio connected!")
        else:
            print(f"   ERROR: {result.stderr.strip()}")
            sys.exit(1)
    except Exception as e:
        print(f"   ERROR: {e}")
        sys.exit(1)

    print()

    # Recording test
    print("2. Microphone test (2 seconds)...")
    try:
        import numpy as np

        proc = subprocess.Popen(
            ["parec", "--raw", "--format=s16le", "--rate=16000", "--channels=1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(2)
        proc.terminate()
        data = proc.stdout.read()
        proc.wait()

        audio = np.frombuffer(data, dtype=np.int16)
        peak = int(np.max(np.abs(audio))) if len(audio) > 0 else 0
        print(f"   Captured {len(audio)} samples ({len(audio)/16000:.1f}s)")
        print(f"   Peak amplitude: {peak}")
        if peak < 100:
            print("   WARNING: Very low audio level. Check your microphone.")
        else:
            print("   Microphone is working!")
    except Exception as e:
        print(f"   ERROR: {e}")

    print()

    # Playback test
    print("3. Speaker test (beep)...")
    try:
        import numpy as np

        sr = 24000
        t = np.linspace(0, 0.3, int(sr * 0.3), endpoint=False)
        beep = (np.sin(2 * np.pi * 440 * t) * 8000).astype(np.int16)

        result = subprocess.run(
            ["paplay", "--raw", "--format=s16le", f"--rate={sr}", "--channels=1"],
            input=beep.tobytes(),
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        if result.returncode == 0:
            print("   Playback complete. Did you hear a beep?")
        else:
            print("   ERROR: paplay failed")
    except Exception as e:
        print(f"   ERROR: {e}")

    print("\n=== Diagnostic complete ===")


if __name__ == "__main__":
    main()
