"""Voice command recording using webrtcvad."""
import logging
import math
import typing
from collections import deque

import webrtcvad

from .const import (
    VoiceCommand,
    VoiceCommandEvent,
    VoiceCommandEventType,
    VoiceCommandRecorder,
    VoiceCommandResult,
)

_LOGGER = logging.getLogger(__name__)

# -----------------------------------------------------------------------------


class WebRtcVadRecorder(VoiceCommandRecorder):
    """Detect speech/silence using webrtcvad."""

    def __init__(
        self,
        vad_mode: int = 3,
        sample_rate: int = 16000,
        chunk_size: int = 960,
        skip_seconds: float = 0,
        min_seconds: float = 1,
        max_seconds: typing.Optional[float] = 30,
        speech_seconds: float = 0.3,
        silence_seconds: float = 0.5,
        before_seconds: float = 0.5,
    ):
        self.vad_mode = vad_mode
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.skip_seconds = skip_seconds
        self.min_seconds = min_seconds
        self.max_seconds = max_seconds
        self.speech_seconds = speech_seconds
        self.silence_seconds = silence_seconds
        self.before_seconds = before_seconds

        # Verify settings
        assert self.vad_mode in range(1, 4), f"VAD mode must be 1-3 (got {vad_mode})"

        chunk_ms = 1000 * ((self.chunk_size / 2) / self.sample_rate)
        assert chunk_ms in [10, 20, 30], (
            "Sample rate and chunk size must make for 10, 20, or 30 ms buffer sizes,"
            + f" assuming 16-bit mono audio (got {chunk_ms} ms)"
        )

        # Voice detector
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(self.vad_mode)

        self.seconds_per_buffer = self.chunk_size / self.sample_rate

        # Store some number of seconds of audio data immediately before voice command starts
        self.before_buffers = int(
            math.ceil(self.before_seconds / self.seconds_per_buffer)
        )

        # Pre-compute values
        self.speech_buffers = int(
            math.ceil(self.speech_seconds / self.seconds_per_buffer)
        )

        self.skip_buffers = int(math.ceil(self.skip_seconds / self.seconds_per_buffer))

        # State
        self.events: typing.List[VoiceCommandEvent] = []
        self.before_phrase_chunks: typing.Deque[bytes] = deque(
            maxlen=self.before_buffers
        )
        self.phrase_buffer: bytes = bytes()

        self.max_buffers: typing.Optional[int] = None
        self.min_phrase_buffers: int = 0
        self.skip_buffers_left: int = 0
        self.speech_buffers_left: int = 0
        self.last_speech: bool = False
        self.in_phrase: bool = False
        self.after_phrase: bool = False
        self.silence_buffers: int = 0
        self.current_seconds: float = 0
        self.current_chunk: bytes = bytes()

    def start(self):
        """Begin new voice command."""

        # State
        self.events.clear()
        self.before_phrase_chunks.clear()
        self.phrase_buffer = bytes()

        if self.max_seconds:
            self.max_buffers = int(
                math.ceil(self.max_seconds / self.seconds_per_buffer)
            )
        else:
            self.max_buffers = None

        self.min_phrase_buffers = int(
            math.ceil(self.min_seconds / self.seconds_per_buffer)
        )

        self.speech_buffers_left = self.speech_buffers
        self.skip_buffers_left = self.skip_buffers
        self.last_speech = False
        self.in_phrase = False
        self.after_phrase = False
        self.silence_buffers = int(
            math.ceil(self.silence_seconds / self.seconds_per_buffer)
        )

        self.current_seconds: float = 0

        self.current_chunk: bytes = bytes()

    def stop(self) -> bytes:
        """Free any resources and return recorded audio."""
        before_buffer = bytes()
        for before_chunk in self.before_phrase_chunks:
            before_buffer += before_chunk

        audio_data = before_buffer + self.phrase_buffer

        # Clear state
        self.before_phrase_chunks.clear()
        self.events.clear()
        self.phrase_buffer = bytes()
        self.current_chunk = bytes()

        # Return leftover audio
        return audio_data

    def process_chunk(self, audio_chunk: bytes) -> typing.Optional[VoiceCommand]:
        """Process a single chunk of audio data."""

        # Add to overall buffer
        self.current_chunk += audio_chunk

        # Process audio in exact chunk(s)
        while len(self.current_chunk) > self.chunk_size:
            # Exctract chunk
            chunk = self.current_chunk[: self.chunk_size]
            self.current_chunk = self.current_chunk[self.chunk_size :]

            if self.skip_buffers_left > 0:
                # Skip audio at beginning
                self.skip_buffers_left -= 1
                continue

            if self.in_phrase:
                self.phrase_buffer += chunk
            else:
                self.before_phrase_chunks.append(chunk)

            self.current_seconds += self.seconds_per_buffer

            # Check maximum number of seconds to record
            if self.max_buffers:
                self.max_buffers -= 1
                if self.max_buffers <= 0:
                    # Timeout
                    _LOGGER.warning("Voice command timeout")
                    return VoiceCommand(
                        result=VoiceCommandResult.FAILURE, events=self.events
                    )

            # Detect speech in chunk
            is_speech = self.vad.is_speech(chunk, self.sample_rate)
            if is_speech and not self.last_speech:
                # Silence -> speech
                self.events.append(
                    VoiceCommandEvent(
                        type=VoiceCommandEventType.SPEECH, time=self.current_seconds
                    )
                )
            elif not is_speech and self.last_speech:
                # Speech -> silence
                self.events.append(
                    VoiceCommandEvent(
                        type=VoiceCommandEventType.SILENCE, time=self.current_seconds
                    )
                )

            self.last_speech = is_speech

            # Handle state changes
            if is_speech and self.speech_buffers_left > 0:
                self.speech_buffers_left -= 1
            elif is_speech and not self.in_phrase:
                # Start of phrase
                self.events.append(
                    VoiceCommandEvent(
                        type=VoiceCommandEventType.STARTED, time=self.current_seconds
                    )
                )
                self.in_phrase = True
                self.after_phrase = False
                self.min_phrase_buffers = int(
                    math.ceil(self.min_seconds / self.seconds_per_buffer)
                )
            elif self.in_phrase and (self.min_phrase_buffers > 0):
                # In phrase, before minimum seconds
                self.min_phrase_buffers -= 1
            elif not is_speech:
                # Outside of speech
                if not self.in_phrase:
                    # Reset
                    self.speech_buffers_left = self.speech_buffers
                elif self.after_phrase and (self.silence_buffers > 0):
                    # After phrase, before stop
                    self.silence_buffers -= 1
                elif self.after_phrase and (self.silence_buffers <= 0):
                    # Phrase complete
                    self.events.append(
                        VoiceCommandEvent(
                            type=VoiceCommandEventType.STOPPED,
                            time=self.current_seconds,
                        )
                    )

                    # Merge before/during command audio data
                    before_buffer = bytes()
                    for before_chunk in self.before_phrase_chunks:
                        before_buffer += before_chunk

                    return VoiceCommand(
                        result=VoiceCommandResult.SUCCESS,
                        audio_data=before_buffer + self.phrase_buffer,
                        events=self.events,
                    )
                elif self.in_phrase and (self.min_phrase_buffers <= 0):
                    # Transition to after phrase
                    self.after_phrase = True
                    self.silence_buffers = int(
                        math.ceil(self.silence_seconds / self.seconds_per_buffer)
                    )

        return None
