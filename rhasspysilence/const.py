"""
Data structures for voice command recording.
"""
import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class VoiceCommandResult(str, Enum):
    """Success/failure of voice command recognition."""

    SUCCESS = "success"
    FAILURE = "failure"


class VoiceCommandEventType(str, Enum):
    """Possible event types during voice command recognition."""

    STARTED = "started"
    SPEECH = "speech"
    SILENCE = "silence"
    STOPPED = "stopped"


@dataclass
class VoiceCommandEvent:
    """Speech/silence events."""

    type: VoiceCommandEventType
    time: float


@dataclass
class VoiceCommand:
    """Result of voice command recognition."""

    result: VoiceCommandResult
    audio_data: typing.Optional[bytes] = None
    events: typing.List[VoiceCommandEvent] = field(default_factory=list)


class VoiceCommandRecorder(ABC):
    """Segment audio into voice command."""

    @abstractmethod
    def start(self):
        """Begin new voice command."""
        pass

    @abstractmethod
    def stop(self) -> bytes:
        """Free any resources and return recorded audio."""
        pass

    @abstractmethod
    def process_chunk(self, audio_chunk: bytes) -> typing.Optional[VoiceCommand]:
        """Process a single chunk of audio data."""
        pass
