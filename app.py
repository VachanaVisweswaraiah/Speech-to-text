import tempfile
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder

import auth
import audio_processor
import config
import monitoring
import storage
import transcriber

# Load environment variables
load_dotenv()
auth.initialize_storage()
storage.initialize_storage()

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


def initialize_session_state() -> None:
    """Set default Streamlit session state values."""
    defaults = {
        "session_id": None,
        "username": None,
        "last_transcript": "",
        "last_filename": None,
        "last_metadata": {},
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def render_auth_controls() -> None:
    """Render login/register controls in the sidebar."""
    st.sidebar.header("Account")

    if st.session_state.username:
        st.sidebar.caption(f"Signed in as {st.session_state.username}")
        if st.sidebar.button("Logout", use_container_width=True):
            auth.logout(st.session_state.session_id)
            monitoring.log_auth_event(st.session_state.username, "logout")
            st.session_state.session_id = None
            st.session_state.username = None
            st.rerun()
        return

    login_tab, register_tab = st.sidebar.tabs(["Login", "Register"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            if auth.authenticate(username, password):
                st.session_state.session_id = auth.create_session(username)
                st.session_state.username = username
                monitoring.log_auth_event(username, "login")
                st.rerun()
            else:
                monitoring.log_auth_event(username, "login", success=False)
                st.sidebar.error("Invalid username or password.")

    with register_tab:
        with st.form("register_form"):
            new_username = st.text_input("Username", key="register_username")
            new_password = st.text_input("Password", type="password", key="register_password")
            submitted = st.form_submit_button("Create account", use_container_width=True)

        if submitted:
            if not new_username or not new_password:
                st.sidebar.error("Username and password are required.")
            elif auth.add_user(new_username, new_password):
                st.session_state.session_id = auth.create_session(new_username)
                st.session_state.username = new_username
                monitoring.log_auth_event(new_username, "signup")
                st.rerun()
            else:
                monitoring.log_auth_event(new_username, "signup", success=False)
                st.sidebar.error("That username is already taken.")


def render_history(username: str) -> None:
    """Render recent saved transcripts for the current user."""
    transcripts = storage.get_user_transcripts(username)
    if not transcripts:
        return

    st.sidebar.header("Recent transcripts")
    for item in transcripts[:5]:
        with st.sidebar.expander(item["filename"]):
            st.caption(item["created_at"])
            st.write(item["preview"])


initialize_session_state()
render_auth_controls()

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

if not st.session_state.username:
    st.info("Log in or create an account to transcribe and save audio.")
    st.stop()

render_history(st.session_state.username)

# -----------------------------
# 🧩 Main UI
# -----------------------------
audio_path = None
source_filename = None
if method == "📂 Upload":
    f = st.file_uploader("Upload an audio file", type=config.AUDIO_FORMATS)
    if f:
        suffix = Path(f.name).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(f.read())
            audio_path = tmp.name
        source_filename = f.name
        st.audio(audio_path)
else:
    st.info("Press to record and release to stop.")
    audio_bytes = audio_recorder(
        pause_threshold=config.AUDIO_RECORDER_PAUSE_THRESHOLD,
        sample_rate=config.SAMPLE_RATE,
    )
    if audio_bytes:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            audio_path = tmp.name
        source_filename = "recording.wav"
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
                started_at = time.monotonic()
                audio_duration = audio_processor.get_audio_duration(audio_path)

                # Set up progress callback
                progress = st.progress(0)

                def update_progress(value: float) -> None:
                    progress.progress(value)

                # Transcribe with progress
                text = transcriber.transcribe_audio_with_callback(
                    audio_path, client, update_progress, chunk_mins * 60
                )

                transcript_name = (
                    f"{Path(source_filename or 'transcript').stem}_" f"{int(time.time())}"
                )
                processing_time = time.monotonic() - started_at
                monitoring.log_transcription(
                    st.session_state.username,
                    source_filename or transcript_name,
                    audio_duration,
                )
                monitoring.perf_monitor.record_transcription(
                    st.session_state.username,
                    audio_duration,
                    processing_time,
                )
                st.session_state.last_transcript = text
                st.session_state.last_filename = transcript_name
                st.session_state.last_metadata = {
                    "source_filename": source_filename,
                    "duration_seconds": audio_duration,
                }
                st.session_state.transcript_editor = text
                st.success("✅ Done!")
            except Exception as e:
                monitoring.log_error(e, context="streamlit_transcription")
                st.error(f"Transcription failed: {e}")

if st.session_state.last_transcript:
    corrected = st.text_area(
        "✍️ Edit transcript:",
        st.session_state.last_transcript,
        height=400,
        key="transcript_editor",
    )
    save_col, download_col = st.columns(2)
    with save_col:
        if st.button("Save transcript", use_container_width=True):
            storage.save_transcript(
                st.session_state.username,
                st.session_state.last_filename,
                corrected,
                st.session_state.last_metadata,
            )
            st.session_state.last_transcript = corrected
            st.success("Transcript saved.")
    with download_col:
        st.download_button(
            "💾 Download",
            corrected,
            "transcript.txt",
            "text/plain",
            use_container_width=True,
        )
