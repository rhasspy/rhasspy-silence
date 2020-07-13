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
    TIMEOUT = "timeout"


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


class SilenceMethod(str, Enum):
    """Method used to determine if an audio frame contains silence.

    Values
    ------
    VAD_ONLY
      Only use webrtcvad

    RATIO_ONLY
      Only use max/current energy ratio threshold

    CURRENT_ONLY
      Only use current energy threshold

    VAD_AND_RATIO
      Use webrtcvad and max/current energy ratio threshold

    VAD_AND_CURRENT
      Use webrtcvad and current energy threshold

    ALL
      Use webrtcvad, max/current energy ratio, and current energy threshold
    """

    VAD_ONLY = "vad_only"
    RATIO_ONLY = "ratio_only"
    CURRENT_ONLY = "current_only"
    VAD_AND_RATIO = "vad_and_ratio"
    VAD_AND_CURRENT = "vad_and_current"
    ALL = "all"
