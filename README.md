# Speech-to-Text Converter

A Streamlit application for converting recorded or uploaded audio into editable transcripts with OpenAI Whisper. The app includes browser recording, file upload, chunked transcription for longer recordings, local user accounts, transcript history, logging, and Docker support.

## Features

- Record audio directly in the browser
- Upload MP3, WAV, and M4A files
- Convert audio to 16 kHz WAV with FFmpeg
- Split long audio into configurable chunks before transcription
- Transcribe audio with the OpenAI Whisper API
- Edit transcripts before saving or downloading
- Save transcript history per user
- Manage local user sessions
- Track logs and transcription performance metrics
- Run locally or with Docker Compose

## Tech Stack

- Python
- Streamlit
- OpenAI API
- FFmpeg / FFprobe
- Pytest
- Black, Flake8, Pylint
- Docker

## Getting Started

### Prerequisites

- Python 3.9+
- FFmpeg installed and available on your `PATH`
- OpenAI API key

Install FFmpeg:

```bash
brew install ffmpeg
sudo apt install ffmpeg
```

### Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Create an environment file:

```bash
cp .env.example .env
```

Then set your API key in `.env`:

```bash
OPENAI_API_KEY=sk-your-api-key-here
```

### Run Locally

```bash
streamlit run app.py
```

The app runs at `http://localhost:8501`.

## Docker

Build and run with Docker Compose:

```bash
docker-compose up --build
```

Production-oriented Compose configuration is available in `docker-compose.prod.yml`.

## Project Structure

```text
Speech-to-text-main/
├── app.py                    # Streamlit UI and application workflow
├── config.py                 # Shared configuration
├── audio_processor.py        # Audio conversion, duration, chunking, cleanup
├── transcriber.py            # OpenAI Whisper transcription layer
├── auth.py                   # Local users and sessions
├── storage.py                # Transcript persistence
├── batch_processor.py        # Batch transcription job utilities
├── monitoring.py             # Logging and performance metrics
├── test_audio_processor.py   # Audio processing tests
├── test_transcriber.py       # Transcription tests
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── API.md
├── ARCHITECTURE.md
├── DEPLOYMENT.md
└── DEVELOPMENT.md
```

## Testing and Quality

Run the test suite:

```bash
uv run pytest test_*.py -v
```

Run formatting and lint checks:

```bash
uv run black --check .
uv run flake8 app.py config.py audio_processor.py transcriber.py auth.py storage.py batch_processor.py monitoring.py test_audio_processor.py test_transcriber.py --max-line-length=100 --extend-ignore=E203,W503
uv run pylint config.py audio_processor.py transcriber.py auth.py storage.py batch_processor.py monitoring.py --exit-zero
```

## Documentation

- [Architecture](ARCHITECTURE.md)
- [API Reference](API.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Development Guide](DEVELOPMENT.md)

## Storage

The app stores local runtime data under `data/` and logs under `logs/`. This keeps local and self-hosted deployments simple. For larger multi-user deployments, replace the JSON file storage with managed database and object storage services.

## Author

Built by [Vachana Visweswaraiah](https://github.com/Vachana33).
