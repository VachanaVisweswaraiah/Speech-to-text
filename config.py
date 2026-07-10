"""
Configuration and constants for Speech-to-Text application.
"""

import os
from typing import List

# Audio processing constants
AUDIO_FORMATS: List[str] = ["mp3", "wav", "m4a"]
SAMPLE_RATE: int = 16000
BIT_DEPTH: str = "pcm_s16le"
DEFAULT_CHUNK_LENGTH_SEC: int = 600  # 10 minutes
MIN_CHUNK_LENGTH_MIN: int = 1
MAX_CHUNK_LENGTH_MIN: int = 10
DEFAULT_CHUNK_LENGTH_MIN: int = 5

# Audio recorder settings
AUDIO_RECORDER_PAUSE_THRESHOLD: float = 2.0

# Whisper API settings
WHISPER_MODEL: str = "whisper-1"

# Streamlit UI settings
PAGE_TITLE: str = "🎙️ Voice to Text"
PAGE_ICON: str = "🎧"
PAGE_LAYOUT: str = "centered"

# Application settings
APP_TITLE: str = "🎧 Voice to Text Converter"
APP_CAPTION: str = "Record or upload an audio file — transcribe it using OpenAI Whisper."


def get_api_key() -> str | None:
    """
    Retrieve OpenAI API key from environment variables.
    
    Returns:
        str | None: API key if available, None otherwise.
    """
    return os.getenv("OPENAI_API_KEY")
