"""Command-line interface to rhasspysilence."""
import argparse
import logging
import sys
import typing
from enum import Enum

from . import WebRtcVadRecorder
from .const import SilenceMethod, VoiceCommandEventType

# -----------------------------------------------------------------------------


class OutputType(str, Enum):
    """Type of printed output."""

    SPEECH_SILENCE = "speech_silence"
    CURRENT_ENERGY = "current_energy"
    MAX_CURRENT_RATIO = "max_current_ratio"


# -----------------------------------------------------------------------------


_LOGGER = logging.getLogger("rhasspysilence")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(prog="rhasspy-silence")
    parser.add_argument(
        "--output-type",
        default=OutputType.SPEECH_SILENCE,
        choices=[e.value for e in OutputType],
        help="Type of printed output",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=960,
        help="Size of audio chunks. Must be 10, 20, or 30 ms for VAD.",
    )
    parser.add_argument(
        "--skip-seconds",
        type=float,
        default=0.0,
        help="Seconds of audio to skip before a voice command",
    )
    parser.add_argument(
        "--max-seconds",
        type=float,
        help="Maximum number of seconds for a voice command",
    )
    parser.add_argument(
        "--min-seconds",
        type=float,
        default=1.0,
        help="Minimum number of seconds for a voice command",
    )
    parser.add_argument(
        "--speech-seconds",
        type=float,
        default=0.3,
        help="Consecutive seconds of speech before start",
    )
    parser.add_argument(
        "--silence-seconds",
        type=float,
        default=0.5,
        help="Consecutive seconds of silence before stop",
    )
    parser.add_argument(
        "--before-seconds",
        type=float,
        default=0.5,
        help="Seconds to record before start",
    )
    parser.add_argument(
        "--sensitivity",
        type=int,
        choices=[1, 2, 3],
        default=3,
        help="VAD sensitivity (1-3)",
    )
    parser.add_argument(
        "--current-threshold",
        type=float,
        help="Debiased energy threshold of current audio frame",
    )
    parser.add_argument(
        "--max-energy",
        type=float,
        help="Fixed maximum energy for ratio calculation (default: observed)",
    )
    parser.add_argument(
        "--max-current-ratio-threshold",
        type=float,
        help="Threshold of ratio between max energy and current audio frame",
    )
    parser.add_argument(
        "--silence-method",
        choices=[e.value for e in SilenceMethod],
        default=SilenceMethod.VAD_ONLY,
        help="Method for detecting silence",
    )

    parser.add_argument(
        "--debug", action="store_true", help="Print DEBUG messages to the console"
    )
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    _LOGGER.debug(args)

    print("Reading raw 16Khz mono audio from stdin...", file=sys.stderr)

    try:
        recorder = WebRtcVadRecorder(
            max_seconds=args.max_seconds,
            vad_mode=args.sensitivity,
            skip_seconds=args.skip_seconds,
            min_seconds=args.min_seconds,
            speech_seconds=args.speech_seconds,
            silence_seconds=args.silence_seconds,
            before_seconds=args.before_seconds,
            silence_method=args.silence_method,
            current_energy_threshold=args.current_threshold,
            max_energy=args.max_energy,
            max_current_ratio_threshold=args.max_current_ratio_threshold,
        )

        dynamic_max_energy = args.max_energy is None
        max_energy: typing.Optional[float] = args.max_energy

        recorder.start()

        while True:
            chunk = sys.stdin.buffer.read(args.chunk_size)
            if not chunk:
                break

            result = recorder.process_chunk(chunk)
            output = ""

            # Print voice command events
            for event in recorder.events:
                if event.type == VoiceCommandEventType.STARTED:
                    output += "["
                elif event.type == VoiceCommandEventType.STOPPED:
                    output += "]"
                elif event.type == VoiceCommandEventType.SPEECH:
                    output += "S"
                elif event.type == VoiceCommandEventType.SILENCE:
                    output += "-"
                elif event.type == VoiceCommandEventType.TIMEOUT:
                    output += "T"

            recorder.events.clear()

            # Print speech/silence
            if args.output_type == OutputType.SPEECH_SILENCE:
                if recorder.last_speech:
                    output += "!"
                else:
                    output += "."
            elif args.output_type == OutputType.CURRENT_ENERGY:
                # Debiased energy of current chunk
                energy = int(WebRtcVadRecorder.get_debiased_energy(chunk))
                output += f"{energy} "
            elif args.output_type == OutputType.MAX_CURRENT_RATIO:
                # Ratio of max/current energy
                energy = WebRtcVadRecorder.get_debiased_energy(chunk)
                if dynamic_max_energy:
                    if max_energy is None:
                        max_energy = energy
                    else:
                        max_energy = max(energy, max_energy)

                assert max_energy is not None, "Max energy not set"
                ratio = max_energy / energy if energy > 0.0 else 0.0
                output += f"{ratio:.2f} "

            print(output, end="", flush=True)

            if result:
                # Reset after voice command
                recorder.stop()
                recorder.start()

    except KeyboardInterrupt:
        pass


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
