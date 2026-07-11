# Development Setup Guide

This guide explains how to set up your local development environment for the Speech-to-Text project using `uv` — a modern, blazingly fast Python package manager.

## Prerequisites

- Python 3.9 or higher
- `uv` installed on your system

### Installing `uv`

#### macOS / Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### Or via Homebrew (macOS)
```bash
brew install uv
```

Verify installation:
```bash
uv --version
```

## Local Development Setup

### 1. Clone the Repository
```bash
git clone https://github.com/VachanaVisweswaraiah/Speech-to-text.git
cd Speech-to-text
```

### 2. Create a Virtual Environment
```bash
uv venv
source .venv/bin/activate  # macOS / Linux
# or
.venv\Scripts\activate  # Windows
```

### 3. Install Dependencies
```bash
uv pip install -r requirements.txt
```

### 4. Set Up Environment Variables
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
OPENAI_API_KEY=sk-your-api-key-here
```

If `.env.example` doesn't exist, create it manually:
```bash
echo "OPENAI_API_KEY=sk-your-api-key-here" > .env
```

### 5. Install FFmpeg (Required for audio processing)

#### macOS
```bash
brew install ffmpeg
```

#### Ubuntu / Debian
```bash
sudo apt-get install ffmpeg
```

#### Windows (via Chocolatey)
```powershell
choco install ffmpeg
```

## Running the Application

### Local Development
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## Testing

### Run All Tests
```bash
uv run pytest test_*.py -v
```

### Run Tests with Coverage
```bash
uv run pytest test_*.py -v --cov=. --cov-report=html
# Open htmlcov/index.html in your browser to view coverage report
```

### Run Specific Test File
```bash
uv run pytest test_audio_processor.py -v
uv run pytest test_transcriber.py -v
```

### Run Tests Matching a Pattern
```bash
uv run pytest test_*.py -k "test_convert" -v
```

## Code Quality & Linting

### Format Code with Black
```bash
uv run black .
```

Check formatting without modifying:
```bash
uv run black --check .
```

### Lint with Pylint
```bash
uv run pylint config.py audio_processor.py transcriber.py auth.py storage.py batch_processor.py monitoring.py
```

### Lint with Flake8
```bash
uv run flake8 app.py config.py audio_processor.py transcriber.py auth.py storage.py batch_processor.py monitoring.py test_audio_processor.py test_transcriber.py --max-line-length=100 --extend-ignore=E203,W503
```

### Security Checks with Bandit
```bash
uv run bandit -r . -ll --skip B101
```

## Running the Full CI Pipeline Locally

To simulate the GitHub Actions pipeline locally:

```bash
# Format check
uv run black --check .

# Linting
uv run pylint config.py audio_processor.py transcriber.py auth.py storage.py batch_processor.py monitoring.py
uv run flake8 app.py config.py audio_processor.py transcriber.py auth.py storage.py batch_processor.py monitoring.py test_audio_processor.py test_transcriber.py --max-line-length=100 --extend-ignore=E203,W503

# Tests with coverage
uv run pytest test_*.py -v --cov=. --cov-report=html

# Security check
uv run bandit -r . -x .venv,__pycache__,.pytest_cache -ll --skip B101
```

## Project Structure

```
speech-to-text/
├── app.py                      # Main Streamlit application
├── config.py                   # Configuration and constants
├── audio_processor.py          # Audio processing utilities
├── transcriber.py              # OpenAI Whisper integration
├── auth.py                     # User and session management
├── storage.py                  # Transcript persistence
├── batch_processor.py          # Batch job utilities
├── monitoring.py               # Logging and metrics
├── test_audio_processor.py     # Tests for audio_processor
├── test_transcriber.py         # Tests for transcriber
├── Dockerfile                  # Container image
├── docker-compose.yml          # Local Docker Compose setup
├── docker-compose.prod.yml     # Production-oriented Compose setup
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project configuration (Black, Pytest, Coverage)
├── .pylintrc                   # Pylint configuration
├── .env.example                # Example environment variables
├── .gitignore                  # Git ignore rules
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI/CD pipeline
├── API.md
├── ARCHITECTURE.md
├── DEPLOYMENT.md
└── README.md                   # Project documentation
```

## Workflow Tips

### Before Committing
Always run the formatters and linters:
```bash
uv run black .
uv run pytest test_*.py -v
```

### Creating a New Feature
1. Create a branch: `git checkout -b feature/my-feature`
2. Install dependencies: `uv pip install -r requirements.txt`
3. Make changes
4. Run tests: `uv run pytest test_*.py -v`
5. Format code: `uv run black .`
6. Commit and push

## Troubleshooting

### "FFmpeg not found"
Make sure FFmpeg is installed and in your PATH:
```bash
ffmpeg -version
ffprobe -version
```

### "OpenAI API key missing"
Ensure your `.env` file exists and contains:
```
OPENAI_API_KEY=sk-your-actual-key
```

### Tests failing due to missing modules
Reinstall dependencies:
```bash
uv pip install -r requirements.txt --force-reinstall
```

### Virtual environment issues
Recreate the environment:
```bash
rm -rf .venv
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Additional Resources

- [uv Documentation](https://docs.astral.sh/uv/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [Pytest Documentation](https://docs.pytest.org/)

## Questions or Issues?

If you encounter any issues, check:
1. Python version: `python --version` (should be 3.9+)
2. uv installation: `uv --version`
3. Virtual environment is activated
4. Dependencies are installed: `uv pip list`
