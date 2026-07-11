"""
User authentication and session management.
"""

import hashlib
import json
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

# Session storage directory
SESSIONS_DIR = Path("data/sessions")
USERS_FILE = Path("data/users.json")
PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 260000
SESSION_ID_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")


def initialize_storage() -> None:
    """Initialize storage directories and files."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not USERS_FILE.exists():
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)


def hash_password(password: str) -> str:
    """
    Hash password using salted PBKDF2-HMAC-SHA256.

    Args:
        password (str): Plain text password.

    Returns:
        str: Hashed password.
    """
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"{PASSWORD_ALGORITHM}${PASSWORD_ITERATIONS}${salt}${digest}"


def _legacy_hash_password(password: str) -> str:
    """Return the legacy unsalted SHA-256 hash for backward compatibility."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify password against hash.

    Args:
        password (str): Plain text password.
        hashed (str): Hashed password.

    Returns:
        bool: True if password matches, False otherwise.
    """
    if hashed.startswith(f"{PASSWORD_ALGORITHM}$"):
        try:
            _, iterations, salt, expected_digest = hashed.split("$", 3)
            digest = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode(),
                salt.encode(),
                int(iterations),
            ).hex()
            return secrets.compare_digest(digest, expected_digest)
        except ValueError:
            return False

    return secrets.compare_digest(_legacy_hash_password(password), hashed)


def get_users() -> Dict[str, str]:
    """
    Load users from storage.

    Returns:
        Dict[str, str]: Dictionary of username -> hashed password.
    """
    initialize_storage()
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def add_user(username: str, password: str) -> bool:
    """
    Add new user.

    Args:
        username (str): Username.
        password (str): Plain text password.

    Returns:
        bool: True if user added, False if already exists.
    """
    username = username.strip()
    if not username or not password:
        return False

    users = get_users()
    if username in users:
        return False

    users[username] = hash_password(password)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)
    return True


def authenticate(username: str, password: str) -> bool:
    """
    Authenticate user.

    Args:
        username (str): Username.
        password (str): Plain text password.

    Returns:
        bool: True if credentials are valid, False otherwise.
    """
    username = username.strip()
    initialize_storage()
    users = get_users()

    if username not in users:
        return False

    return verify_password(password, users[username])


def create_session(username: str) -> str:
    """
    Create user session.

    Args:
        username (str): Username.

    Returns:
        str: Session token.
    """
    username = username.strip()
    initialize_storage()
    session_id = secrets.token_urlsafe(32)

    session_data = {
        "username": username,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
    }

    session_file = SESSIONS_DIR / f"{session_id}.json"
    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2)

    return session_id


def verify_session(session_id: str) -> Optional[str]:
    """
    Verify session and return username if valid.

    Args:
        session_id (str): Session token.

    Returns:
        str or None: Username if session is valid, None otherwise.
    """
    initialize_storage()
    if not session_id or any(char not in SESSION_ID_CHARS for char in session_id):
        return None

    session_file = SESSIONS_DIR / f"{session_id}.json"

    if not session_file.exists():
        return None

    with open(session_file, "r", encoding="utf-8") as f:
        session_data = json.load(f)

    expires_at = datetime.fromisoformat(session_data["expires_at"])
    if datetime.now() > expires_at:
        session_file.unlink()
        return None

    return session_data["username"]


def logout(session_id: str) -> None:
    """
    Logout user by deleting session.

    Args:
        session_id (str): Session token.
    """
    if not session_id or any(char not in SESSION_ID_CHARS for char in session_id):
        return

    session_file = SESSIONS_DIR / f"{session_id}.json"
    if session_file.exists():
        session_file.unlink()


def change_password(username: str, old_password: str, new_password: str) -> bool:
    """
    Change user password.

    Args:
        username (str): Username.
        old_password (str): Current password.
        new_password (str): New password.

    Returns:
        bool: True if password changed, False otherwise.
    """
    username = username.strip()
    if not new_password or not authenticate(username, old_password):
        return False

    users = get_users()
    users[username] = hash_password(new_password)

    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

    return True
