# API Reference

This document provides comprehensive API documentation for the Speech-to-Text application.

## Module: `config`

Central configuration and constants management.

### Constants

| Name | Type | Value | Description |
|------|------|-------|-------------|
| `AUDIO_FORMATS` | List[str] | ["mp3", "wav", "m4a"] | Supported audio file formats |
| `SAMPLE_RATE` | int | 16000 | Audio sample rate in Hz (Whisper requirement) |
| `BIT_DEPTH` | str | "pcm_s16le" | Audio bit depth format |
| `DEFAULT_CHUNK_LENGTH_SEC` | int | 600 | Default chunk length in seconds (10 min) |
| `WHISPER_MODEL` | str | "whisper-1" | OpenAI Whisper model identifier |
| `PAGE_TITLE` | str | "🎙️ Voice to Text" | Browser tab title |
| `PAGE_LAYOUT` | str | "centered" | Streamlit page layout mode |

### Functions

#### `get_api_key() -> str | None`

Retrieves the OpenAI API key from environment variables.

**Returns:**
- `str` | `None`: API key if available, None otherwise.

**Example:**
```python
from config import get_api_key
api_key = get_api_key()
if api_key:
    print("API key is configured")
else:
    print("API key is missing")
```

---

## Module: `audio_processor`

Audio file conversion, chunking, and processing utilities.

### Functions

#### `convert_to_wav(input_path: str) -> str`

Converts audio file to 16-bit WAV format at 16kHz sample rate for Whisper compatibility.

**Parameters:**
- `input_path` (str): Path to input audio file (mp3, wav, m4a)

**Returns:**
- `str`: Path to converted WAV file

**Raises:**
- `RuntimeError`: If ffmpeg conversion fails

**Example:**
```python
import audio_processor
wav_file = audio_processor.convert_to_wav("recording.mp3")
```

#### `get_audio_duration(input_path: str) -> float`

Gets the duration of an audio file in seconds using ffprobe.

**Parameters:**
- `input_path` (str): Path to audio file

**Returns:**
- `float`: Duration in seconds

**Raises:**
- `RuntimeError`: If ffprobe fails
- `ValueError`: If duration cannot be parsed

**Example:**
```python
duration = audio_processor.get_audio_duration("audio.wav")
print(f"Audio is {duration:.2f} seconds long")
```

#### `split_audio_ffmpeg(input_path: str, chunk_length_sec: int = 600) -> List[str]`

Splits audio file into chunks using ffmpeg. Useful for handling long audio files that exceed API limits.

**Parameters:**
- `input_path` (str): Path to input audio file
- `chunk_length_sec` (int): Length of each chunk in seconds (default: 600 = 10 min)

**Returns:**
- `List[str]`: List of paths to chunk files

**Raises:**
- `RuntimeError`: If audio duration cannot be determined or splitting fails

**Example:**
```python
# Split 30-minute audio into 5-minute chunks
chunks = audio_processor.split_audio_ffmpeg("long_audio.wav", chunk_length_sec=300)
print(f"Created {len(chunks)} chunks")
```

#### `cleanup_temp_files(file_paths: List[str]) -> None`

Cleans up temporary audio files.

**Parameters:**
- `file_paths` (List[str]): List of file paths to remove

**Example:**
```python
chunks = ["/tmp/chunk_0.wav", "/tmp/chunk_1.wav"]
audio_processor.cleanup_temp_files(chunks)
```

---

## Module: `transcriber`

OpenAI Whisper integration for audio transcription.

### Functions

#### `initialize_client(api_key: str) -> OpenAI`

Initializes OpenAI client with API key validation.

**Parameters:**
- `api_key` (str): OpenAI API key

**Returns:**
- `OpenAI`: Initialized OpenAI client

**Raises:**
- `ValueError`: If API key is empty

**Example:**
```python
from transcriber import initialize_client
client = initialize_client("sk-your-api-key")
```

#### `transcribe_audio(file_path: str, client: OpenAI, chunk_length_sec: int = 600) -> str`

Transcribes audio file using OpenAI Whisper API. Automatically handles long audio by splitting into chunks.

**Parameters:**
- `file_path` (str): Path to audio file (mp3, wav, m4a)
- `client` (OpenAI): Initialized OpenAI client
- `chunk_length_sec` (int): Length of chunks in seconds (default: 600)

**Returns:**
- `str`: Transcribed text from all chunks

**Raises:**
- `RuntimeError`: If transcription fails

**Example:**
```python
from transcriber import initialize_client, transcribe_audio
client = initialize_client("sk-your-api-key")
text = transcribe_audio("recording.wav", client)
print(text)
```

#### `transcribe_audio_with_callback(file_path: str, client: OpenAI, progress_callback: callable = None, chunk_length_sec: int = 600) -> str`

Transcribes audio with progress callback for UI updates.

**Parameters:**
- `file_path` (str): Path to audio file
- `client` (OpenAI): Initialized OpenAI client
- `progress_callback` (callable, optional): Function to call with progress (0.0-1.0)
- `chunk_length_sec` (int): Length of chunks in seconds (default: 600)

**Returns:**
- `str`: Transcribed text from all chunks

**Example:**
```python
def on_progress(value: float):
    print(f"Progress: {value*100:.1f}%")

text = transcriber.transcribe_audio_with_callback(
    "audio.wav", 
    client, 
    on_progress,
    chunk_length_sec=600
)
```

---

## Streamlit Application: `app.py`

Main user-facing web application built with Streamlit.

### Features

- **Authentication**: Local login/register/logout flow
- **Audio Input**: Upload or record audio directly
- **Settings Sidebar**: Configure chunk length and input method
- **Real-time Progress**: Live progress bar during transcription
- **Editing Interface**: Edit transcript in browser
- **Transcript History**: Save edited transcripts for the logged-in user
- **Download**: Export transcript as text file

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for Whisper access |

### Page Configuration

- **Title**: 🎧 Voice to Text Converter
- **Layout**: Centered
- **Responsive**: Works on desktop and tablet

---

## Error Handling

All modules follow consistent error handling patterns:

### Exception Hierarchy

```
Exception
├── ValueError
│   └── Invalid API keys or configuration
├── RuntimeError
│   ├── FFmpeg/FFprobe failures
│   ├── Transcription service failures
│   └── Audio processing errors
└── OSError
    └── File system operations
```

### Example Error Handling

```python
from transcriber import transcribe_audio
from audio_processor import split_audio_ffmpeg

try:
    text = transcribe_audio("audio.wav", client)
except RuntimeError as e:
    print(f"Transcription failed: {e}")
except ValueError as e:
    print(f"Configuration error: {e}")
```

---

## Performance Considerations

### Audio Chunking Strategy

- Default chunk length: 10 minutes (600 seconds)
- Configurable via UI slider: 1-10 minutes
- Optimizes API reliability and costs

### Concurrency Limits

- Sequential chunk processing (prevents API rate limiting)
- Each chunk processed independently
- Progress tracked and reported to UI

### Temporary File Management

- Converted WAV and chunk files are cleaned up after processing
- Cleanup runs on success and error
- Uploaded/recorded source temp files are short-lived Streamlit runtime inputs
- Uses system temp directory

---

## Module: `auth`

Local JSON-backed user and session management.

### Primary Functions

- `initialize_storage() -> None`: Creates auth storage files/directories.
- `add_user(username: str, password: str) -> bool`: Adds a user if the username is available.
- `authenticate(username: str, password: str) -> bool`: Verifies credentials.
- `create_session(username: str) -> str`: Creates a 24-hour session token.
- `verify_session(session_id: str) -> str | None`: Returns the username for a valid session.
- `logout(session_id: str) -> None`: Deletes a session file.
- `change_password(username: str, old_password: str, new_password: str) -> bool`: Updates a password after verifying the old one.

## Module: `storage`

Local JSON-backed transcript persistence.

### Primary Functions

- `save_transcript(username: str, filename: str, text: str, metadata: dict | None = None) -> bool`
- `load_transcript(username: str, filename: str) -> dict | None`
- `get_user_transcripts(username: str) -> list[dict]`
- `search_transcripts(username: str, query: str) -> list[dict]`
- `delete_transcript(username: str, filename: str) -> bool`
- `get_storage_stats(username: str) -> dict`

Usernames and transcript filenames are normalized before being used as path components.

## Module: `monitoring`

Application logging and performance metrics.

### Primary Functions

- `initialize_logging(log_level: str = "INFO", log_file: str | None = None)`
- `log_event(event_type: str, username: str | None = None, details: dict | None = None, severity: str = "INFO")`
- `log_transcription(username: str, filename: str, duration_seconds: float, status: str = "success")`
- `log_auth_event(username: str, event: str, success: bool = True)`
- `log_error(error: Exception, context: str | None = None)`
- `cleanup_old_logs(days: int = 30) -> int`
- `PerformanceMonitor.record_transcription(...)`
- `PerformanceMonitor.get_stats() -> dict`

---

## Testing

All modules include comprehensive test coverage:

```bash
# Run all tests
pytest test_*.py -v

# Run specific test file
pytest test_audio_processor.py -v

# Generate coverage report
pytest test_*.py --cov=. --cov-report=html
```

### Test Files

- `test_audio_processor.py` - Audio processing pipeline tests
- `test_transcriber.py` - Transcription service tests

---

## Dependencies

See [requirements.txt](requirements.txt) for current versions.

**Core Dependencies:**
- `streamlit` - Web UI framework
- `openai` - OpenAI API client
- `python-dotenv` - Environment variable management
- `audio-recorder-streamlit` - In-browser audio recording

**System Dependencies:**
- `ffmpeg` - Audio processing
- `ffprobe` - Audio metadata extraction

---

## Development

For local development setup, see [DEVELOPMENT.md](DEVELOPMENT.md).

For architecture overview, see [ARCHITECTURE.md](ARCHITECTURE.md).

For deployment guide, see [DEPLOYMENT.md](DEPLOYMENT.md).
