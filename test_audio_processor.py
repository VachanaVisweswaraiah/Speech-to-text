"""
Unit tests for audio_processor module.
"""

import unittest
from unittest.mock import MagicMock, patch, mock_open
import tempfile
import os

import audio_processor
import config


class TestAudioProcessorConfig(unittest.TestCase):
    """Test audio processor configuration constants."""

    def test_audio_formats_defined(self):
        """Verify audio formats are defined."""
        self.assertIsInstance(config.AUDIO_FORMATS, list)
        self.assertGreater(len(config.AUDIO_FORMATS), 0)
        self.assertIn("mp3", config.AUDIO_FORMATS)
        self.assertIn("wav", config.AUDIO_FORMATS)
        self.assertIn("m4a", config.AUDIO_FORMATS)

    def test_sample_rate_is_valid(self):
        """Verify sample rate is 16kHz for Whisper compatibility."""
        self.assertEqual(config.SAMPLE_RATE, 16000)

    def test_whisper_model_defined(self):
        """Verify Whisper model is defined."""
        self.assertEqual(config.WHISPER_MODEL, "whisper-1")

    def test_chunk_length_defaults(self):
        """Verify chunk length defaults are reasonable."""
        self.assertEqual(config.DEFAULT_CHUNK_LENGTH_SEC, 600)
        self.assertEqual(config.DEFAULT_CHUNK_LENGTH_MIN, 5)
        self.assertGreaterEqual(config.MIN_CHUNK_LENGTH_MIN, 1)
        self.assertGreaterEqual(config.MAX_CHUNK_LENGTH_MIN, 10)


class TestConvertToWav(unittest.TestCase):
    """Test convert_to_wav function."""

    @patch("subprocess.run")
    def test_convert_to_wav_creates_output(self, mock_run):
        """Test that convert_to_wav calls ffmpeg with correct parameters."""
        input_file = "/tmp/input.mp3"

        result = audio_processor.convert_to_wav(input_file)

        # Verify subprocess.run was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]

        # Verify ffmpeg command includes required parameters
        self.assertIn("ffmpeg", call_args)
        self.assertIn(input_file, call_args)
        self.assertIn("pcm_s16le", call_args)
        self.assertIn("16000", call_args)

        # Verify result is a path
        self.assertIsInstance(result, str)
        self.assertTrue(result.endswith(".wav"))

    @patch("subprocess.run")
    def test_convert_to_wav_ffmpeg_error(self, mock_run):
        """Test that convert_to_wav raises error on ffmpeg failure."""
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "ffmpeg")

        with self.assertRaises(RuntimeError) as context:
            audio_processor.convert_to_wav("/tmp/input.mp3")

        self.assertIn("Failed to convert", str(context.exception))


class TestGetAudioDuration(unittest.TestCase):
    """Test get_audio_duration function."""

    @patch("subprocess.run")
    def test_get_audio_duration_success(self, mock_run):
        """Test successful duration retrieval."""
        mock_result = MagicMock()
        mock_result.stdout = "120.5"
        mock_run.return_value = mock_result

        duration = audio_processor.get_audio_duration("/tmp/audio.wav")

        self.assertEqual(duration, 120.5)
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        self.assertIn("ffprobe", call_args)

    @patch("subprocess.run")
    def test_get_audio_duration_invalid_format(self, mock_run):
        """Test error handling for invalid duration format."""
        mock_result = MagicMock()
        mock_result.stdout = "invalid"
        mock_run.return_value = mock_result

        with self.assertRaises(ValueError):
            audio_processor.get_audio_duration("/tmp/audio.wav")

    @patch("subprocess.run")
    def test_get_audio_duration_ffprobe_error(self, mock_run):
        """Test error handling when ffprobe fails."""
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "ffprobe")

        with self.assertRaises(RuntimeError) as context:
            audio_processor.get_audio_duration("/tmp/audio.wav")

        self.assertIn("Failed to get audio duration", str(context.exception))


class TestSplitAudioFfmpeg(unittest.TestCase):
    """Test split_audio_ffmpeg function."""

    @patch("audio_processor.get_audio_duration")
    @patch("subprocess.run")
    def test_split_audio_single_chunk(self, mock_run, mock_duration):
        """Test that files shorter than chunk length return single chunk."""
        mock_duration.return_value = 300  # 5 minutes
        mock_run.return_value = MagicMock()

        chunks = audio_processor.split_audio_ffmpeg("/tmp/audio.wav", chunk_length_sec=600)

        self.assertEqual(len(chunks), 1)
        mock_run.assert_called_once()

    @patch("audio_processor.get_audio_duration")
    @patch("subprocess.run")
    def test_split_audio_multiple_chunks(self, mock_run, mock_duration):
        """Test that long files are split into multiple chunks."""
        mock_duration.return_value = 1500  # 25 minutes
        mock_run.return_value = MagicMock()

        chunks = audio_processor.split_audio_ffmpeg("/tmp/audio.wav", chunk_length_sec=600)

        # 1500 / 600 = 2.5, so ceil(2.5) = 3 chunks
        self.assertEqual(len(chunks), 3)
        self.assertEqual(mock_run.call_count, 3)

    @patch("audio_processor.get_audio_duration")
    @patch("subprocess.run")
    def test_split_audio_chunks_are_paths(self, mock_run, mock_duration):
        """Test that split_audio returns valid file paths."""
        mock_duration.return_value = 1200
        mock_run.return_value = MagicMock()

        chunks = audio_processor.split_audio_ffmpeg("/tmp/audio.wav", chunk_length_sec=600)

        for chunk in chunks:
            self.assertIsInstance(chunk, str)
            self.assertTrue(chunk.endswith(".wav"))

    @patch("audio_processor.get_audio_duration")
    @patch("subprocess.run")
    def test_split_audio_ffmpeg_error(self, mock_run, mock_duration):
        """Test error handling when ffmpeg fails during splitting."""
        import subprocess

        mock_duration.return_value = 1200
        mock_run.side_effect = subprocess.CalledProcessError(1, "ffmpeg")

        with self.assertRaises(RuntimeError) as context:
            audio_processor.split_audio_ffmpeg("/tmp/audio.wav")

        self.assertIn("Failed to split audio", str(context.exception))


class TestCleanupTempFiles(unittest.TestCase):
    """Test cleanup_temp_files function."""

    def test_cleanup_removes_files(self):
        """Test that cleanup_temp_files removes existing files."""
        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False) as f1:
            file1 = f1.name
        with tempfile.NamedTemporaryFile(delete=False) as f2:
            file2 = f2.name

        # Verify files exist
        self.assertTrue(os.path.exists(file1))
        self.assertTrue(os.path.exists(file2))

        # Clean up
        audio_processor.cleanup_temp_files([file1, file2])

        # Verify files are deleted
        self.assertFalse(os.path.exists(file1))
        self.assertFalse(os.path.exists(file2))

    def test_cleanup_handles_missing_files(self):
        """Test that cleanup_temp_files handles non-existent files gracefully."""
        # This should not raise an exception
        audio_processor.cleanup_temp_files(["/tmp/nonexistent_file_xyz.wav"])

    def test_cleanup_empty_list(self):
        """Test that cleanup_temp_files handles empty list."""
        # This should not raise an exception
        audio_processor.cleanup_temp_files([])


if __name__ == "__main__":
    unittest.main()
