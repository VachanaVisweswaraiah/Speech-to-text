# 🎙️ Speech-to-Text Converter

A practical AI application for converting recorded or uploaded audio into editable transcripts using OpenAI Whisper. The project combines a polished Streamlit interface with backend audio processing so long recordings can be handled reliably in chunks.

## Why this project matters

This project demonstrates a strong foundation in:
- AI product development
- Python-based application building
- API integration with modern LLM and speech models
- UI/UX for real-world tools
- End-to-end workflow design from upload to downloadable output

## Key capabilities

- Record audio directly in the browser or upload an existing file
- Transcribe MP3, WAV, and M4A audio
- Split long recordings into manageable chunks for reliable processing
- Review and edit the transcript in the browser
- Download the final transcript as a plain text file

## Tech stack

- Frontend/UI: Streamlit
- Speech-to-text: OpenAI Whisper API
- Audio handling: FFmpeg, pydub
- Environment management: python-dotenv
- Deployment target: Streamlit Cloud or any Python hosting environment

## Project structure

```text
Speech-to-text-main/
├── app.py
├── README.md
├── requirements.txt
├── .gitignore
└── .devcontainer/
```

## Local setup

1. Clone the repository

```bash
git clone https://github.com/VachanaVisweswaraiah/Speech-to-text.git
cd Speech-to-text
```

2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

3. Add your OpenAI API key

```bash
export OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
```

4. Install FFmpeg

```bash
brew install ffmpeg            # macOS
sudo apt install ffmpeg        # Ubuntu / Linux
```

5. Run the app

```bash
streamlit run app.py
```

## What makes this a strong portfolio project

This is a good portfolio project because it shows that you can take an AI workflow from idea to usable interface. It is especially relevant for someone building a profile around applied AI, LLM systems, and product-focused engineering.

## Future enhancements

- Add authentication and user accounts
- Support batch transcription jobs
- Add speaker diarization
- Introduce summarization and keyword extraction
- Add testing, logging, and CI/CD

## Author

Built by [Vachana Visweswaraiah](https://github.com/Vachana33).