"""Tests for rhasspysilence."""
import unittest
import wave

from rhasspysilence import WebRtcVadRecorder, VoiceCommandResult

class RhasspySilenceTestCase(unittest.TestCase):
    """Tests for rhasspysilence."""

    def __init__(self, *args):
        super().__init__(*args)

        self.recorder = None
        self.chunk_size = 2048

    def setUp(self):
        self.recorder = WebRtcVadRecorder()
        self.recorder.start()

    def test_command(self):
        """Verify voice command sample WAV file."""
        command = None

        # Check test WAV file
        with wave.open("etc/turn_on_living_room_lamp.wav", "r") as wav_file:
            audio_data = wav_file.readframes(wav_file.getnframes())
            while audio_data:
                chunk = audio_data[:self.chunk_size]
                audio_data = audio_data[self.chunk_size:]

                command = self.recorder.process_chunk(chunk)
                if command:
                    break

            self.assertTrue(command)
            self.assertEqual(command.result, VoiceCommandResult.SUCCESS)
            self.assertGreater(len(command.audio_data), 0)

    def test_noise(self):
        """Verify no command in noise WAV file."""
        command = None

        # Check test WAV file
        with wave.open("etc/noise.wav", "r") as wav_file:
            audio_data = wav_file.readframes(wav_file.getnframes())
            while audio_data:
                chunk = audio_data[:self.chunk_size]
                audio_data = audio_data[self.chunk_size:]

                command = self.recorder.process_chunk(chunk)
                if command:
                    break

            self.assertFalse(command)
