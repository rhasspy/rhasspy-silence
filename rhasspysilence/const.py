"""
Data structures for voice command recording.
"""
from abc import ABC, abstractmethod
from enum import Enum
import typing

import attr


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


@attr.s
class VoiceCommandEvent:
    """Speech/silence events."""

    type: VoiceCommandEventType = attr.ib()
    time: float = attr.ib()


@attr.s
class VoiceCommand:
    """Result of voice command recognition."""

    result: VoiceCommandResult = attr.ib()
    audio_data: typing.Optional[bytes] = attr.ib(default=None)
    events: typing.List[VoiceCommandEvent] = attr.ib(factory=list)


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
