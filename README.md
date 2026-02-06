# Malone AI

A personal AI assistant with real-time voice interaction, smart home control, network management, and web automation.

## Quick Start

```bash
# Install
pip install -e .

# Check audio devices (WSL2)
python scripts/check_audio.py

# Test Ollama connection
python scripts/test_ollama.py

# Run
python -m malone
```

## Configuration

Copy `.env.example` to `.env` and fill in your API keys. Edit `config.yaml` for runtime settings.

## Architecture

```
Mic → VAD (Silero) → STT (faster-whisper) → LLM (Ollama/Claude) → TTS (edge-tts) → Speaker
```
