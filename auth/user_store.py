import json
import hashlib
from pathlib import Path

USER_DB_PATH = Path("data/users.json")


def _hash_password(password: str) -> str:
    """Return SHA-256 hash of the password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def load_users() -> dict:
    """Load user database from JSON. Return empty dict if missing."""
    if not USER_DB_PATH.exists():
        return {}
    try:
        with USER_DB_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_users(users: dict) -> None:
    """Write user database to JSON."""
    USER_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with USER_DB_PATH.open("w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)


def create_user(username: str, password: str) -> bool:
    """Create a new user. Return False if username exists."""
    users = load_users()
    if username in users:
        return False

    users[username] = _hash_password(password)
    save_users(users)
    return True


def authenticate_user(username: str, password: str) -> bool:
    """Return True if username exists and password matches."""
    users = load_users()
    if username not in users:
        return False

    return users[username] == _hash_password(password)
