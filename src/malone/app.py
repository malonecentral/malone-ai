from __future__ import annotations

from malone.audio.capture import AudioCapture
from malone.audio.playback import AudioPlayback
from malone.audio.vad import VoiceActivityDetector
from malone.config.settings import get_settings
from malone.conversation.loop import ConversationLoop
from malone.conversation.manager import ConversationManager
from malone.llm.ollama_client import OllamaClient
from malone.stt.transcriber import Transcriber
from malone.tts.synthesizer import TTSSynthesizer


class MaloneApp:
    """Main application - wires all components together."""

    def __init__(self):
        self.settings = get_settings()

    async def run(self):
        print("Malone AI starting up...")
        print()

        # Initialize components
        print("  Loading voice activity detection...")
        vad = VoiceActivityDetector(threshold=self.settings.vad.threshold)

        print("  Loading speech recognition...")
        transcriber = Transcriber(
            model_size=self.settings.stt.model_size,
            device=self.settings.stt.device,
            compute_type=self.settings.stt.compute_type,
        )

        print("  Connecting to Ollama...")
        llm = OllamaClient(self.settings.ollama)

        audio_capture = AudioCapture(
            sample_rate=self.settings.audio.sample_rate,
            channels=self.settings.audio.channels,
            blocksize=self.settings.audio.blocksize,
            device=self.settings.audio.input_device,
        )

        audio_playback = AudioPlayback(
            sample_rate=24000,  # edge-tts output rate
            device=self.settings.audio.output_device,
        )

        tts = TTSSynthesizer(
            voice=self.settings.tts.voice,
            rate=self.settings.tts.rate,
            volume=self.settings.tts.volume,
        )

        conversation = ConversationManager(
            system_prompt=self.settings.system_prompt,
        )

        loop = ConversationLoop(
            audio_capture=audio_capture,
            audio_playback=audio_playback,
            vad=vad,
            transcriber=transcriber,
            llm=llm,
            tts=tts,
            conversation=conversation,
            silence_threshold=self.settings.vad.silence_threshold,
            min_speech_duration=self.settings.vad.min_speech_duration,
        )

        print()
        print("Malone is ready. Start speaking!")
        print("Press Ctrl+C to exit.")
        print()

        await loop.run()
