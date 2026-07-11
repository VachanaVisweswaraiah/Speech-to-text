"""
Transcript storage and history management.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Storage directory
TRANSCRIPTS_DIR = Path("data/transcripts")
SAFE_NAME_PATTERN = re.compile(r"[^A-Za-z0-9_.-]+")


def initialize_storage() -> None:
    """Initialize storage directory."""
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_component(value: str) -> str:
    """Convert user-provided names to safe path components."""
    cleaned = SAFE_NAME_PATTERN.sub("_", value).strip("._")
    return cleaned or "untitled"


def save_transcript(
    username: str, filename: str, text: str, metadata: Optional[Dict] = None
) -> bool:
    """
    Save transcript to file.

    Args:
        username (str): Username.
        filename (str): Transcript filename (without extension).
        text (str): Transcript text.
        metadata (Dict, optional): Additional metadata to store.

    Returns:
        bool: True if saved successfully.
    """
    initialize_storage()

    safe_username = _safe_component(username)
    safe_filename = _safe_component(filename)
    user_dir = TRANSCRIPTS_DIR / safe_username
    user_dir.mkdir(parents=True, exist_ok=True)

    transcript_data = {
        "filename": safe_filename,
        "text": text,
        "created_at": datetime.now().isoformat(),
        "metadata": metadata or {},
    }

    transcript_file = user_dir / f"{safe_filename}.json"
    with open(transcript_file, "w", encoding="utf-8") as f:
        json.dump(transcript_data, f, indent=2)

    return True


def load_transcript(username: str, filename: str) -> Optional[Dict]:
    """
    Load transcript from file.

    Args:
        username (str): Username.
        filename (str): Transcript filename (without extension).

    Returns:
        Dict or None: Transcript data if found, None otherwise.
    """
    initialize_storage()

    transcript_file = (
        TRANSCRIPTS_DIR / _safe_component(username) / f"{_safe_component(filename)}.json"
    )

    if not transcript_file.exists():
        return None

    with open(transcript_file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_user_transcripts(username: str) -> List[Dict]:
    """
    Get all transcripts for a user.

    Args:
        username (str): Username.

    Returns:
        List[Dict]: List of transcript metadata.
    """
    initialize_storage()

    user_dir = TRANSCRIPTS_DIR / _safe_component(username)

    if not user_dir.exists():
        return []

    transcripts = []
    for transcript_file in sorted(user_dir.glob("*.json"), reverse=True):
        with open(transcript_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            transcripts.append(
                {
                    "filename": data["filename"],
                    "created_at": data["created_at"],
                    "preview": data["text"][:100] + "..."
                    if len(data["text"]) > 100
                    else data["text"],
                    "length": len(data["text"]),
                }
            )

    return transcripts


def delete_transcript(username: str, filename: str) -> bool:
    """
    Delete transcript.

    Args:
        username (str): Username.
        filename (str): Transcript filename (without extension).

    Returns:
        bool: True if deleted, False if not found.
    """
    transcript_file = (
        TRANSCRIPTS_DIR / _safe_component(username) / f"{_safe_component(filename)}.json"
    )

    if not transcript_file.exists():
        return False

    transcript_file.unlink()
    return True


def search_transcripts(username: str, query: str) -> List[Dict]:
    """
    Search user's transcripts for a query string.

    Args:
        username (str): Username.
        query (str): Search query.

    Returns:
        List[Dict]: List of matching transcripts.
    """
    initialize_storage()

    user_transcripts = get_user_transcripts(username)
    query_lower = query.lower()

    return [
        t
        for t in user_transcripts
        if query_lower in t["preview"].lower() or query_lower in t["filename"].lower()
    ]


def get_storage_stats(username: str) -> Dict:
    """
    Get storage statistics for a user.

    Args:
        username (str): Username.

    Returns:
        Dict: Storage statistics.
    """
    initialize_storage()

    user_dir = TRANSCRIPTS_DIR / _safe_component(username)

    if not user_dir.exists():
        return {"count": 0, "total_size_mb": 0.0, "oldest": None, "newest": None}

    transcript_files = list(user_dir.glob("*.json"))

    if not transcript_files:
        return {"count": 0, "total_size_mb": 0.0, "oldest": None, "newest": None}

    total_size = sum(f.stat().st_size for f in transcript_files)
    created_times = []
    for transcript_file in transcript_files:
        with open(transcript_file, "r", encoding="utf-8") as f:
            created_times.append(json.load(f)["created_at"])

    return {
        "count": len(transcript_files),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "oldest": min(created_times),
        "newest": max(created_times),
    }
