"""Command-line interface to rhasspysilence."""
import argparse
import io
import logging
import sys
import typing
import wave
from enum import Enum
from pathlib import Path

from . import WebRtcVadRecorder
from .const import SilenceMethod, VoiceCommandEventType
from .utils import trim_silence

# -----------------------------------------------------------------------------


class OutputType(str, Enum):
    """Type of printed output."""

    SPEECH_SILENCE = "speech_silence"
    CURRENT_ENERGY = "current_energy"
    MAX_CURRENT_RATIO = "max_current_ratio"
    NONE = "none"


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

    # Splitting and trimming by silence
    parser.add_argument(
        "--split-dir",
        help="Split incoming audio by silence and write WAV file(s) to directory",
    )
    parser.add_argument(
        "--split-format",
        default="{}.wav",
        help="Format for split file names (default: '{}.wav', only with --split-dir)",
    )
    parser.add_argument(
        "--trim-silence",
        action="store_true",
        help="Trim silence when splitting (only with --split-dir)",
    )
    parser.add_argument(
        "--trim-ratio",
        default=20.0,
        type=float,
        help="Max/current energy ratio used to detect silence (only with --trim-silence)",
    )
    parser.add_argument(
        "--trim-chunk-size",
        default=960,
        type=int,
        help="Size of audio chunks for detecting silence (only with --trim-silence)",
    )
    parser.add_argument(
        "--trim-keep-before",
        default=0,
        type=int,
        help="Number of audio chunks before speech to keep (only with --trim-silence)",
    )
    parser.add_argument(
        "--trim-keep-after",
        default=0,
        type=int,
        help="Number of audio chunks after speech to keep (only with --trim-silence)",
    )

    parser.add_argument("--quiet", action="store_true", help="Set output type to none")

    parser.add_argument(
        "--debug", action="store_true", help="Print DEBUG messages to the console"
    )
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    _LOGGER.debug(args)

    if args.quiet or (args.trim_silence and not args.split_dir):
        args.output_type = OutputType.NONE

    if args.split_dir:
        # Directory to write WAV file(s) split by silence
        args.split_dir = Path(args.split_dir)
        args.split_dir.mkdir(parents=True, exist_ok=True)

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
        split_index = 0

        recorder.start()

        while True:
            chunk = sys.stdin.buffer.read(args.chunk_size)
            if not chunk:
                break

            result = recorder.process_chunk(chunk)
            output = ""

            if args.output_type != OutputType.NONE:
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
                audio_bytes = recorder.stop()

                if args.split_dir:
                    # Split audio
                    if args.trim_silence:
                        audio_bytes = trim_silence(
                            audio_bytes,
                            chunk_size=args.trim_chunk_size,
                            ratio_threshold=args.trim_ratio,
                            keep_chunks_before=args.trim_keep_before,
                            keep_chunks_after=args.trim_keep_after,
                        )

                    split_wav_path = args.split_dir / args.split_format.format(
                        split_index
                    )

                    wav_file: wave.Wave_write = wave.open(str(split_wav_path), "wb")
                    with wav_file:
                        wav_file.setframerate(recorder.sample_rate)
                        wav_file.setsampwidth(2)
                        wav_file.setnchannels(1)
                        wav_file.writeframes(audio_bytes)

                    _LOGGER.info("Wrote %s", split_wav_path)
                    split_index += 1
                elif args.trim_silence:
                    # Trim silence without splitting
                    audio_bytes = trim_silence(
                        audio_bytes,
                        chunk_size=args.trim_chunk_size,
                        ratio_threshold=args.trim_ratio,
                        keep_chunks_before=args.trim_keep_before,
                        keep_chunks_after=args.trim_keep_after,
                    )

                    with io.BytesIO() as wav_io:
                        wav_file: wave.Wave_write = wave.open(wav_io, "wb")
                        with wav_file:
                            wav_file.setframerate(recorder.sample_rate)
                            wav_file.setsampwidth(2)
                            wav_file.setnchannels(1)
                            wav_file.writeframes(audio_bytes)

                        sys.stdout.buffer.write(wav_io.getvalue())

                    break

                recorder.start()

    except KeyboardInterrupt:
        pass


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
