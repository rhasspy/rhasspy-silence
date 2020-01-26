"""Tests for rhasspysilence."""
import wave

from rhasspysilence import VoiceCommandResult, WebRtcVadRecorder

CHUNK_SIZE = 2048


def test_command():
    """Verify voice command sample WAV file."""
    command = None
    recorder = WebRtcVadRecorder()
    recorder.start()

    # Check test WAV file
    with wave.open("etc/turn_on_living_room_lamp.wav", "r") as wav_file:
        audio_data = wav_file.readframes(wav_file.getnframes())
        while audio_data:
            chunk = audio_data[:CHUNK_SIZE]
            audio_data = audio_data[CHUNK_SIZE:]

            command = recorder.process_chunk(chunk)
            if command:
                break

        assert command
        assert command.result == VoiceCommandResult.SUCCESS
        assert command.audio_data


def test_noise():
    """Verify no command in noise WAV file."""
    command = None
    recorder = WebRtcVadRecorder()
    recorder.start()

    # Check test WAV file
    with wave.open("etc/noise.wav", "r") as wav_file:
        audio_data = wav_file.readframes(wav_file.getnframes())
        while audio_data:
            chunk = audio_data[:CHUNK_SIZE]
            audio_data = audio_data[CHUNK_SIZE:]

            command = recorder.process_chunk(chunk)
            if command:
                break

        assert not command
