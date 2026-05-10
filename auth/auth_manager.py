"""
auth/auth_manager.py

Hardened authentication manager for Risk Battle Game A.

Security controls:
  - Per-user salted PBKDF2-HMAC-SHA256 password hashing
  - Timing-safe digest comparison via hmac.compare_digest
  - Consecutive-failure attempt counter persisted to disk
  - Account lockout after MAX_ATTEMPTS failures
  - LOCKOUT_SECONDS cooldown before retry is permitted
  - Failure logging with UTC timestamp to auth_failures.log
"""

import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MAX_ATTEMPTS: int = 5           # Consecutive failures before lockout
LOCKOUT_SECONDS: int = 900      # 15-minute lockout window
HASH_ITERATIONS: int = 260_000  # PBKDF2 iterations (OWASP 2023 recommendation)
HASH_ALGORITHM: str = "sha256"

# Paths resolved relative to this file so the module is location-independent
_AUTH_DIR = Path(__file__).parent
USER_STORE_PATH    = _AUTH_DIR / ".." / "data" / "users.json"
LOCKOUT_STORE_PATH = _AUTH_DIR / ".." / "data" / "lockout_state.json"
FAILURE_LOG_PATH   = _AUTH_DIR / ".." / "data" / "auth_failures.log"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    """Load a JSON file, returning an empty dict if missing or corrupt."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_json(path: Path, data: dict) -> None:
    """Atomically write *data* to *path* as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    tmp.replace(path)  # atomic on POSIX; best-effort on Windows


def _log_failure(username: str, reason: str) -> None:
    """Append a single failure record to the auth failure log."""
    FAILURE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    with open(FAILURE_LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(f"{ts}  FAILURE  user={username!r}  reason={reason}\n")


# ---------------------------------------------------------------------------
# Password utilities
# ---------------------------------------------------------------------------

def hash_password(password: str) -> Tuple[str, str]:
    """
    Hash *password* using PBKDF2-HMAC-SHA256 with a fresh random 32-byte salt.

    Returns:
        (hex_hash, hex_salt) both as hex strings safe for JSON storage.
    """
    salt = os.urandom(32)
    digest = hashlib.pbkdf2_hmac(
        HASH_ALGORITHM,
        password.encode("utf-8"),
        salt,
        HASH_ITERATIONS,
    )
    return digest.hex(), salt.hex()


def _verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
    """
    Verify *password* against a (hash, salt) pair.

    Uses hmac.compare_digest for timing-safe comparison — prevents
    timing-based username/password enumeration attacks.
    """
    salt = bytes.fromhex(stored_salt)
    candidate = hashlib.pbkdf2_hmac(
        HASH_ALGORITHM,
        password.encode("utf-8"),
        salt,
        HASH_ITERATIONS,
    )
    return hmac.compare_digest(candidate.hex(), stored_hash)


# ---------------------------------------------------------------------------
# Lockout state
# ---------------------------------------------------------------------------

def _load_lockout() -> dict:
    return _load_json(LOCKOUT_STORE_PATH)


def _save_lockout(state: dict) -> None:
    _save_json(LOCKOUT_STORE_PATH, state)


def _is_locked_out(username: str) -> Tuple[bool, float]:
    """
    Return (locked_out, seconds_remaining).

    locked_out is True only when the lockout window has not yet expired.
    Expired lockouts are cleared automatically.
    """
    state = _load_lockout()
    record = state.get(username, {})

    if not record or record.get("attempts", 0) < MAX_ATTEMPTS:
        return False, 0.0

    locked_at = record.get("locked_at", 0.0)
    elapsed = time.time() - locked_at

    if elapsed < LOCKOUT_SECONDS:
        return True, LOCKOUT_SECONDS - elapsed

    # Lockout window expired — auto-reset
    _reset_attempts(username)
    return False, 0.0


def _record_failure(username: str) -> int:
    """
    Increment the consecutive failure counter for *username*.
    Stamps locked_at timestamp when MAX_ATTEMPTS is reached.
    Returns the new failure count.
    """
    state = _load_lockout()
    record = state.setdefault(username, {"attempts": 0, "locked_at": 0.0})
    record["attempts"] += 1
    if record["attempts"] >= MAX_ATTEMPTS:
        record["locked_at"] = time.time()
    _save_lockout(state)
    return record["attempts"]


def _reset_attempts(username: str) -> None:
    """Clear the failure counter for *username* after a successful login."""
    state = _load_lockout()
    state.pop(username, None)
    _save_lockout(state)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class AuthManager:
    """
    Hardened authentication manager for Risk Battle Game A.

    Security controls active on every login call:
        1. Lockout gate  — checked before any DB lookup to frustrate enumeration
        2. Dummy hash    — executed even for unknown users to prevent timing leaks
        3. PBKDF2 verify — 260 000 iterations + per-user salt
        4. Timing-safe   — hmac.compare_digest on all hash comparisons
        5. Auto-lockout  — account locked after MAX_ATTEMPTS consecutive failures
        6. Failure log   — every failure written to auth_failures.log with UTC ts

    Usage:
        am = AuthManager()
        am.register("alice", "correct-horse-battery-staple")
        result = am.login("alice", "correct-horse-battery-staple")
        if result["success"]:
            ...
        else:
            print(result["reason"])
    """

    def __init__(self, store_path: Optional[Path] = None) -> None:
        self._store = Path(store_path) if store_path else USER_STORE_PATH

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, username: str, password: str) -> bool:
        """
        Register a new user.

        Passwords are stored as salted PBKDF2-HMAC-SHA256 hashes — never
        in plain text. Returns True on success, False if username is taken.
        """
        users = _load_json(self._store)
        if username in users:
            return False
        pw_hash, pw_salt = hash_password(password)
        users[username] = {"hash": pw_hash, "salt": pw_salt}
        _save_json(self._store, users)
        return True

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def login(self, username: str, password: str) -> dict:
        """
        Attempt to authenticate *username* with *password*.

        Return dict schema:
            Success:  {"success": True}
            Failure:  {"success": False, "reason": str,
                       "locked": bool, "seconds_remaining": float}
        """
        # 1. Lockout gate — evaluated before any DB lookup
        locked, remaining = _is_locked_out(username)
        if locked:
            minutes = int(remaining // 60) + 1
            reason = (
                f"Account locked after {MAX_ATTEMPTS} consecutive failures. "
                f"Try again in {minutes} minute(s)."
            )
            _log_failure(username, "LOCKED_OUT")
            return {
                "success": False,
                "reason": reason,
                "locked": True,
                "seconds_remaining": remaining,
            }

        # 2. Load user store
        users = _load_json(self._store)

        if username not in users:
            # Dummy hash keeps response time uniform regardless of existence
            _verify_password(password, "0" * 64, "0" * 64)
            attempts = _record_failure(username)
            _log_failure(username, "UNKNOWN_USER")
            return self._failure_response(username, attempts)

        # 3. Timing-safe password verification
        record = users[username]
        if not _verify_password(password, record["hash"], record["salt"]):
            attempts = _record_failure(username)
            _log_failure(username, "WRONG_PASSWORD")
            return self._failure_response(username, attempts)

        # 4. Success — clear failure state
        _reset_attempts(username)
        return {"success": True}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _failure_response(username: str, attempts: int) -> dict:
        remaining_attempts = max(0, MAX_ATTEMPTS - attempts)
        if remaining_attempts == 0:
            reason = (
                f"Account locked after {MAX_ATTEMPTS} failed attempts. "
                f"Try again in {LOCKOUT_SECONDS // 60} minute(s)."
            )
            locked = True
        else:
            reason = (
                f"Invalid credentials. "
                f"{remaining_attempts} attempt(s) remaining before lockout."
            )
            locked = False
        return {
            "success": False,
            "reason": reason,
            "locked": locked,
            "seconds_remaining": float(LOCKOUT_SECONDS) if locked else 0.0,
        }

    def is_locked(self, username: str) -> Tuple[bool, float]:
        """Expose lockout status for UI/CLI layer queries."""
        return _is_locked_out(username)

    def reset_lockout(self, username: str) -> None:
        """Admin-level reset — clears lockout and attempt counter for *username*."""
        _reset_attempts(username)
