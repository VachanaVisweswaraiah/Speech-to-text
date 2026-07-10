import streamlit as st
import os, tempfile, math, subprocess
from dotenv import load_dotenv
from openai import OpenAI
from audio_recorder_streamlit import audio_recorder

# -----------------------------
# 🎨 App setup
# -----------------------------
st.set_page_config(page_title="🎙️ Voice to Text", page_icon="🎧", layout="centered")
st.title("🎧 Voice to Text Converter")
st.caption("Record or upload an audio file — transcribe it using OpenAI Whisper.")

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = None

if not api_key:
    st.warning("⚠️ Add your OpenAI API key in .env or Streamlit Secrets.")
else:
    client = OpenAI(api_key=api_key)

# -----------------------------
# 🧰 Helper: convert & chunk with ffmpeg
# -----------------------------
def convert_to_wav(input_path):
    """Ensure the file is 16-bit WAV for Whisper"""
    output_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    cmd = ["ffmpeg", "-y", "-i", input_path, "-acodec", "pcm_s16le", "-ar", "16000", output_path]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path

def split_audio_ffmpeg(input_path, chunk_length_sec=600):
    """Split long audio via ffmpeg into N-minute chunks"""
    # Get total duration
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", input_path],
        capture_output=True, text=True
    )
    duration = float(result.stdout.strip())
    parts = math.ceil(duration / chunk_length_sec)
    paths = []
    for i in range(parts):
        start = i * chunk_length_sec
        output = tempfile.NamedTemporaryFile(suffix=f"_part{i}.wav", delete=False).name
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-ss", str(start),
             "-t", str(chunk_length_sec), output],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        paths.append(output)
    return paths

# -----------------------------
# 🧠 Transcription
# -----------------------------
def transcribe_audio(path, chunk_length_sec=600):
    if not client:
        st.error("OpenAI API key is missing. Please configure it first.")
        return ""

    wav_path = convert_to_wav(path)
    chunks = split_audio_ffmpeg(wav_path, chunk_length_sec)
    full_text = ""
    progress = st.progress(0)
    for i, cpath in enumerate(chunks):
        with open(cpath, "rb") as f:
            text = client.audio.transcriptions.create(model="whisper-1", file=f).text
        full_text += f"\n--- Chunk {i+1} ---\n{text}\n"
        progress.progress((i + 1) / len(chunks))
    return full_text.strip()

# -----------------------------
# 🎛️ Sidebar controls
# -----------------------------
st.sidebar.header("⚙️ Settings")
method = st.sidebar.radio("Input method", ("🎙️ Record", "📂 Upload"))
chunk_mins = st.sidebar.slider("Chunk length (min)", 1, 10, 5)
st.sidebar.caption("Developed by Vachana Visweswaraiah")

# -----------------------------
# 🧩 Main UI
# -----------------------------
audio_path = None
if method == "📂 Upload":
    f = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a"])
    if f:
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.write(f.read())
        audio_path = tmp.name
        st.audio(audio_path)
else:
    st.info("Press to record and release to stop.")
    audio_bytes = audio_recorder(pause_threshold=2.0, sample_rate=16000)
    if audio_bytes:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.write(audio_bytes)
        audio_path = tmp.name
        st.audio(audio_path)
        st.success("✅ Recording ready.")

# -----------------------------
# ▶️ Run transcription
# -----------------------------
if audio_path and st.button("🚀 Start Transcription", use_container_width=True):
    with st.spinner("Transcribing..."):
        text = transcribe_audio(audio_path, chunk_mins * 60)
        st.success("✅ Done!")
        corrected = st.text_area("✍️ Edit transcript:", text, height=400)
        st.download_button("💾 Download", corrected, "transcript.txt", "text/plain", use_container_width=True)
