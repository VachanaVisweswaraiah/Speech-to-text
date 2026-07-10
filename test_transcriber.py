"""
Unit tests for transcriber module.
"""

import unittest
from unittest.mock import MagicMock, patch, Mock

import transcriber
import config


class TestInitializeClient(unittest.TestCase):
    """Test initialize_client function."""

    @patch("transcriber.OpenAI")
    def test_initialize_client_with_valid_key(self, mock_openai):
        """Test successful client initialization."""
        api_key = "sk-test-key-12345"
        mock_openai.return_value = MagicMock()

        client = transcriber.initialize_client(api_key)

        mock_openai.assert_called_once_with(api_key=api_key)
        self.assertIsNotNone(client)

    def test_initialize_client_with_empty_key(self):
        """Test that empty API key raises ValueError."""
        with self.assertRaises(ValueError) as context:
            transcriber.initialize_client("")

        self.assertIn("API key cannot be empty", str(context.exception))

    def test_initialize_client_with_none_key(self):
        """Test that None API key raises ValueError."""
        with self.assertRaises(ValueError) as context:
            transcriber.initialize_client(None)

        self.assertIn("API key cannot be empty", str(context.exception))


class TestTranscribeAudio(unittest.TestCase):
    """Test transcribe_audio function."""

    @patch("transcriber.audio_processor.split_audio_ffmpeg")
    @patch("transcriber.audio_processor.convert_to_wav")
    def test_transcribe_single_chunk_success(self, mock_convert, mock_split):
        """Test successful transcription of single chunk."""
        # Setup mocks
        mock_convert.return_value = "/tmp/audio.wav"
        mock_split.return_value = ["/tmp/chunk_0.wav"]

        mock_client = MagicMock()
        mock_transcription = MagicMock()
        mock_transcription.text = "Hello world"
        mock_client.audio.transcriptions.create.return_value = mock_transcription

        # Test transcription
        with patch("builtins.open", create=True) as mock_file:
            mock_file.return_value.__enter__.return_value = MagicMock()
            result = transcriber.transcribe_audio("/tmp/input.mp3", mock_client)

        self.assertEqual(result, "Hello world")
        mock_convert.assert_called_once()
        mock_split.assert_called_once()

    @patch("transcriber.audio_processor.split_audio_ffmpeg")
    @patch("transcriber.audio_processor.convert_to_wav")
    def test_transcribe_multiple_chunks(self, mock_convert, mock_split):
        """Test transcription of multiple chunks."""
        # Setup mocks
        mock_convert.return_value = "/tmp/audio.wav"
        mock_split.return_value = ["/tmp/chunk_0.wav", "/tmp/chunk_1.wav"]

        mock_client = MagicMock()

        # Create different transcriptions for each chunk
        chunk_1_transcription = MagicMock()
        chunk_1_transcription.text = "First part"
        chunk_2_transcription = MagicMock()
        chunk_2_transcription.text = "Second part"

        mock_client.audio.transcriptions.create.side_effect = [
            chunk_1_transcription,
            chunk_2_transcription,
        ]

        # Test transcription
        with patch("builtins.open", create=True):
            result = transcriber.transcribe_audio("/tmp/input.mp3", mock_client)

        # Verify chunk separators are included
        self.assertIn("Chunk 1", result)
        self.assertIn("Chunk 2", result)
        self.assertIn("First part", result)
        self.assertIn("Second part", result)
        self.assertEqual(mock_client.audio.transcriptions.create.call_count, 2)

    @patch("transcriber.audio_processor.convert_to_wav")
    def test_transcribe_audio_convert_error(self, mock_convert):
        """Test error handling when audio conversion fails."""
        mock_convert.side_effect = RuntimeError("FFmpeg error")
        mock_client = MagicMock()

        with self.assertRaises(RuntimeError) as context:
            transcriber.transcribe_audio("/tmp/input.mp3", mock_client)

        self.assertIn("Transcription failed", str(context.exception))

    @patch("transcriber.audio_processor.split_audio_ffmpeg")
    @patch("transcriber.audio_processor.convert_to_wav")
    def test_transcribe_audio_api_error(self, mock_convert, mock_split):
        """Test error handling when Whisper API fails."""
        mock_convert.return_value = "/tmp/audio.wav"
        mock_split.return_value = ["/tmp/chunk_0.wav"]

        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.side_effect = Exception("API Error")

        with patch("builtins.open", create=True):
            with self.assertRaises(RuntimeError) as context:
                transcriber.transcribe_audio("/tmp/input.mp3", mock_client)

        self.assertIn("Transcription failed", str(context.exception))


class TestTranscribeAudioWithCallback(unittest.TestCase):
    """Test transcribe_audio_with_callback function."""

    @patch("transcriber.audio_processor.split_audio_ffmpeg")
    @patch("transcriber.audio_processor.convert_to_wav")
    def test_transcribe_with_callback_called(self, mock_convert, mock_split):
        """Test that progress callback is called."""
        # Setup mocks
        mock_convert.return_value = "/tmp/audio.wav"
        mock_split.return_value = ["/tmp/chunk_0.wav", "/tmp/chunk_1.wav"]

        mock_client = MagicMock()
        mock_transcription = MagicMock()
        mock_transcription.text = "Test"
        mock_client.audio.transcriptions.create.return_value = mock_transcription

        # Track callback calls
        callback_calls = []

        def progress_callback(value):
            callback_calls.append(value)

        # Test transcription
        with patch("builtins.open", create=True):
            transcriber.transcribe_audio_with_callback(
                "/tmp/input.mp3", mock_client, progress_callback
            )

        # Verify callback was called for each chunk
        self.assertEqual(len(callback_calls), 2)
        self.assertAlmostEqual(callback_calls[0], 0.5)  # 1/2
        self.assertAlmostEqual(callback_calls[1], 1.0)  # 2/2

    @patch("transcriber.audio_processor.split_audio_ffmpeg")
    @patch("transcriber.audio_processor.convert_to_wav")
    def test_transcribe_with_none_callback(self, mock_convert, mock_split):
        """Test that None callback is handled gracefully."""
        # Setup mocks
        mock_convert.return_value = "/tmp/audio.wav"
        mock_split.return_value = ["/tmp/chunk_0.wav"]

        mock_client = MagicMock()
        mock_transcription = MagicMock()
        mock_transcription.text = "Test"
        mock_client.audio.transcriptions.create.return_value = mock_transcription

        # This should not raise an exception with None callback
        with patch("builtins.open", create=True):
            result = transcriber.transcribe_audio_with_callback(
                "/tmp/input.mp3", mock_client, None
            )

        self.assertIsNotNone(result)


class TestConfigIntegration(unittest.TestCase):
    """Test configuration integration with transcriber."""

    def test_whisper_model_constant_used(self):
        """Verify that transcriber uses the configured Whisper model."""
        self.assertEqual(config.WHISPER_MODEL, "whisper-1")


if __name__ == "__main__":
    unittest.main()
