"""
Audio processing utilities for converting and chunking audio files.
"""

import math
import subprocess
import tempfile
from pathlib import Path
from typing import List

import config


def convert_to_wav(input_path: str) -> str:
    """
    Convert audio file to 16-bit WAV format at 16kHz sample rate.

    This ensures compatibility with OpenAI Whisper API requirements.

    Args:
        input_path (str): Path to input audio file.

    Returns:
        str: Path to converted WAV file.

    Raises:
        subprocess.CalledProcessError: If ffmpeg conversion fails.
    """
    output_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-acodec",
        config.BIT_DEPTH,
        "-ar",
        str(config.SAMPLE_RATE),
        output_path,
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to convert audio to WAV: {e}")
    return output_path


def get_audio_duration(input_path: str) -> float:
    """
    Get the duration of an audio file in seconds using ffprobe.

    Args:
        input_path (str): Path to audio file.

    Returns:
        float: Duration in seconds.

    Raises:
        subprocess.CalledProcessError: If ffprobe fails.
        ValueError: If duration cannot be parsed.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                input_path,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return float(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get audio duration: {e}") from e
    except ValueError as e:
        raise ValueError(f"Could not parse duration from ffprobe output: {e}") from e


def split_audio_ffmpeg(input_path: str, chunk_length_sec: int = 600) -> List[str]:
    """
    Split audio file into chunks using ffmpeg.

    This is useful for handling long audio files that exceed API limits.

    Args:
        input_path (str): Path to input audio file.
        chunk_length_sec (int): Length of each chunk in seconds. Defaults to 600 (10 min).

    Returns:
        List[str]: List of paths to chunk files.

    Raises:
        RuntimeError: If audio duration cannot be determined or splitting fails.
    """
    duration = get_audio_duration(input_path)
    num_chunks = math.ceil(duration / chunk_length_sec)
    paths = []

    for i in range(num_chunks):
        start = i * chunk_length_sec
        with tempfile.NamedTemporaryFile(suffix=f"_part{i}.wav", delete=False) as tmp_file:
            output = tmp_file.name
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-ss",
            str(start),
            "-t",
            str(chunk_length_sec),
            output,
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            paths.append(output)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to split audio chunk {i}: {e}")

    return paths


def cleanup_temp_files(file_paths: List[str]) -> None:
    """
    Clean up temporary audio files.

    Args:
        file_paths (List[str]): List of file paths to remove.
    """
    for path in file_paths:
        try:
            Path(path).unlink(missing_ok=True)
        except OSError as e:
            print(f"Warning: Could not delete {path}: {e}")
