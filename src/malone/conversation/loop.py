from __future__ import annotations

import asyncio
from enum import Enum, auto

from malone.audio.capture import AudioCapture
from malone.audio.playback import AudioPlayback
from malone.audio.vad import VoiceActivityDetector
from malone.conversation.manager import ConversationManager
from malone.llm.base import LLMClient
from malone.stt.transcriber import Transcriber
from malone.tts.synthesizer import TTSSynthesizer


class State(Enum):
    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    SPEAKING = auto()


class ConversationLoop:
    """Main voice conversation loop: listen → transcribe → think → speak."""

    def __init__(
        self,
        audio_capture: AudioCapture,
        audio_playback: AudioPlayback,
        vad: VoiceActivityDetector,
        transcriber: Transcriber,
        llm: LLMClient,
        tts: TTSSynthesizer,
        conversation: ConversationManager,
        silence_threshold: float = 0.8,
        min_speech_duration: float = 0.3,
    ):
        self.audio_capture = audio_capture
        self.audio_playback = audio_playback
        self.vad = vad
        self.transcriber = transcriber
        self.llm = llm
        self.tts = tts
        self.conversation = conversation
        self.silence_threshold = silence_threshold
        self.min_speech_duration = min_speech_duration

        self.state = State.IDLE
        self._audio_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=200)
        self._loop: asyncio.AbstractEventLoop | None = None

    async def run(self):
        """Run the conversation loop until interrupted."""
        self._loop = asyncio.get_event_loop()
        self.audio_capture.start(callback=self._on_audio_chunk)

        try:
            while True:
                speech_audio = await self._collect_speech()
                if speech_audio is None:
                    continue

                self.state = State.PROCESSING

                # Transcribe speech to text
                text = await asyncio.to_thread(
                    self.transcriber.transcribe, speech_audio
                )
                if not text.strip():
                    self.state = State.IDLE
                    continue

                print(f"\n  You: {text}")

                # Get LLM response
                self.conversation.add_user(text)
                response = await self.llm.chat(self.conversation.get_messages())
                reply = response.content
                self.conversation.add_assistant(reply)

                print(f"  Malone: {reply}")

                # Speak the response
                self.state = State.SPEAKING
                try:
                    audio_data = await self.tts.synthesize(reply)
                    await self.audio_playback.play(audio_data)
                except Exception as e:
                    print(f"  [TTS error: {e}]")

                # Drain any audio captured during TTS playback (echo prevention)
                while not self._audio_queue.empty():
                    try:
                        self._audio_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                # Brief pause to let echo fade before listening again
                await asyncio.sleep(0.5)
                self.vad.reset()
                self.state = State.IDLE
        finally:
            self.audio_capture.stop()

    async def _collect_speech(self) -> bytes | None:
        """Collect audio until a complete utterance is detected via VAD."""
        self.state = State.IDLE
        speech_buffer = bytearray()
        speech_active = False
        silence_duration = 0.0
        chunk_duration = self.audio_capture.blocksize / self.audio_capture.sample_rate

        while True:
            try:
                chunk = await asyncio.wait_for(
                    self._audio_queue.get(), timeout=0.1
                )
            except asyncio.TimeoutError:
                continue

            # Ignore audio while speaking (prevent echo)
            if self.state == State.SPEAKING:
                continue

            is_speech = self.vad.is_speech(chunk, self.audio_capture.sample_rate)

            if is_speech and not speech_active:
                # Speech onset
                speech_active = True
                self.state = State.LISTENING
                silence_duration = 0.0
                speech_buffer.extend(chunk)

            elif is_speech and speech_active:
                silence_duration = 0.0
                speech_buffer.extend(chunk)

            elif not is_speech and speech_active:
                speech_buffer.extend(chunk)
                silence_duration += chunk_duration

                # End of utterance after enough silence
                if silence_duration >= self.silence_threshold:
                    total_duration = len(speech_buffer) / (
                        self.audio_capture.sample_rate * 2  # int16 = 2 bytes
                    )
                    if total_duration >= self.min_speech_duration:
                        return bytes(speech_buffer)
                    # Too short, discard
                    speech_buffer.clear()
                    speech_active = False
                    silence_duration = 0.0
                    self.vad.reset()
                    self.state = State.IDLE

    def _on_audio_chunk(self, indata, frames, time_info, status):
        """Callback from sounddevice audio thread."""
        if status:
            print(f"  [Audio: {status}]")
        audio_bytes = indata.tobytes()
        try:
            self._audio_queue.put_nowait(audio_bytes)
        except asyncio.QueueFull:
            pass  # Drop frame if queue is full
