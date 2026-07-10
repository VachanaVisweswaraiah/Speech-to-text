import tempfile

import streamlit as st
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder

import config
import transcriber

# Load environment variables
load_dotenv()

# -----------------------------
# 🎨 App setup
# -----------------------------
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout=config.PAGE_LAYOUT,
)
st.title(config.APP_TITLE)
st.caption(config.APP_CAPTION)

# Initialize OpenAI client
api_key = config.get_api_key()
client = None

if not api_key:
    st.warning("⚠️ Add your OpenAI API key in .env or Streamlit Secrets.")
else:
    try:
        client = transcriber.initialize_client(api_key)
    except ValueError as e:
        st.error(f"Failed to initialize OpenAI client: {e}")

# -----------------------------
# 🎛️ Sidebar controls
# -----------------------------
st.sidebar.header("⚙️ Settings")
method = st.sidebar.radio("Input method", ("🎙️ Record", "📂 Upload"))
chunk_mins = st.sidebar.slider(
    "Chunk length (min)",
    config.MIN_CHUNK_LENGTH_MIN,
    config.MAX_CHUNK_LENGTH_MIN,
    config.DEFAULT_CHUNK_LENGTH_MIN,
)
st.sidebar.caption("Developed by Vachana Visweswaraiah")

# -----------------------------
# 🧩 Main UI
# -----------------------------
audio_path = None
if method == "📂 Upload":
    f = st.file_uploader("Upload an audio file", type=config.AUDIO_FORMATS)
    if f:
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.write(f.read())
        audio_path = tmp.name
        st.audio(audio_path)
else:
    st.info("Press to record and release to stop.")
    audio_bytes = audio_recorder(
        pause_threshold=config.AUDIO_RECORDER_PAUSE_THRESHOLD,
        sample_rate=config.SAMPLE_RATE,
    )
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
    if not client:
        st.error("OpenAI API key is missing. Please configure it first.")
    else:
        with st.spinner("Transcribing..."):
            try:
                # Set up progress callback
                progress = st.progress(0)

                def update_progress(value: float) -> None:
                    progress.progress(value)

                # Transcribe with progress
                text = transcriber.transcribe_audio_with_callback(
                    audio_path, client, update_progress, chunk_mins * 60
                )

                st.success("✅ Done!")
                corrected = st.text_area("✍️ Edit transcript:", text, height=400)
                st.download_button(
                    "💾 Download",
                    corrected,
                    "transcript.txt",
                    "text/plain",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Transcription failed: {e}")
