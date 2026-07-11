"""
Transcription utilities using OpenAI Whisper API.
"""

from typing import Callable, Optional

from openai import OpenAI

import audio_processor
import config


def initialize_client(api_key: str) -> OpenAI:
    """
    Initialize OpenAI client with API key.

    Args:
        api_key (str): OpenAI API key.

    Returns:
        OpenAI: Initialized OpenAI client.

    Raises:
        ValueError: If API key is empty.
    """
    if not api_key:
        raise ValueError("API key cannot be empty")
    return OpenAI(api_key=api_key)


def transcribe_audio(file_path: str, client: OpenAI, chunk_length_sec: int = 600) -> str:
    """
    Transcribe audio file using OpenAI Whisper API.

    Automatically handles long audio by splitting into chunks
    and concatenating transcriptions.

    Args:
        file_path (str): Path to audio file (mp3, wav, m4a).
        client (OpenAI): Initialized OpenAI client.
        chunk_length_sec (int): Length of chunks in seconds. Defaults to 600 (10 min).

    Returns:
        str: Transcribed text from all chunks.

    Raises:
        RuntimeError: If transcription fails.
    """
    wav_path = None
    chunks = []

    try:
        # Convert to WAV format
        wav_path = audio_processor.convert_to_wav(file_path)

        # Split into chunks if needed
        chunks = audio_processor.split_audio_ffmpeg(wav_path, chunk_length_sec)

        # Transcribe each chunk
        full_text = ""
        for i, chunk_path in enumerate(chunks):
            try:
                with open(chunk_path, "rb") as f:
                    transcription = client.audio.transcriptions.create(
                        model=config.WHISPER_MODEL, file=f
                    )
                    text = transcription.text

                # Add chunk separator if multiple chunks
                if len(chunks) > 1:
                    full_text += f"\n--- Chunk {i + 1} ---\n{text}\n"
                else:
                    full_text += text
            except Exception as e:
                raise RuntimeError(f"Failed to transcribe chunk {i}: {e}") from e

        return full_text.strip()

    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}") from e
    finally:
        temp_files = [path for path in [wav_path, *chunks] if path]
        audio_processor.cleanup_temp_files(temp_files)


def transcribe_audio_with_callback(
    file_path: str,
    client: OpenAI,
    progress_callback: Optional[Callable[[float], None]] = None,
    chunk_length_sec: int = 600,
) -> str:
    """
    Transcribe audio with progress callback for UI updates.

    Args:
        file_path (str): Path to audio file.
        client (OpenAI): Initialized OpenAI client.
        progress_callback (callable, optional): Function to call with progress (0.0-1.0).
        chunk_length_sec (int): Length of chunks in seconds. Defaults to 600 (10 min).

    Returns:
        str: Transcribed text from all chunks.
    """
    wav_path = None
    chunks = []

    try:
        # Convert to WAV format
        wav_path = audio_processor.convert_to_wav(file_path)

        # Split into chunks if needed
        chunks = audio_processor.split_audio_ffmpeg(wav_path, chunk_length_sec)

        # Transcribe each chunk with progress
        full_text = ""
        for i, chunk_path in enumerate(chunks):
            try:
                with open(chunk_path, "rb") as f:
                    transcription = client.audio.transcriptions.create(
                        model=config.WHISPER_MODEL, file=f
                    )
                    text = transcription.text

                # Add chunk separator if multiple chunks
                if len(chunks) > 1:
                    full_text += f"\n--- Chunk {i + 1} ---\n{text}\n"
                else:
                    full_text += text

                # Call progress callback if provided
                if progress_callback:
                    progress_callback((i + 1) / len(chunks))
            except Exception as e:
                raise RuntimeError(f"Failed to transcribe chunk {i}: {e}") from e

        return full_text.strip()

    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}") from e
    finally:
        temp_files = [path for path in [wav_path, *chunks] if path]
        audio_processor.cleanup_temp_files(temp_files)
