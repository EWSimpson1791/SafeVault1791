# auth/dcrypt.py
"""
Cryptographic utilities for password hashing and verification.

Algorithm  : PBKDF2-HMAC-SHA256
Iterations : 260,000  (OWASP 2023 minimum)
Salt       : 32 bytes (256-bit) via os.urandom
Comparison : hmac.compare_digest  (timing-safe)

Hash format
-----------
v2 (current) : "v2:<base64(salt[32] + pbkdf2_digest[32])>"
Legacy (v1)  : plain base64, no prefix  (SHA-256 single-round, 16-byte salt)
               verify_password() accepts both; needs_rehash() flags v1 hashes
               for upgrade on the next successful login.
"""

import base64
import hashlib
import hmac
import os
from typing import Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ITERATIONS = 260_000
_SALT_BYTES = 32        # 256-bit salt
_HASH_BYTES = 32        # 256-bit PBKDF2 output
_V2_PREFIX  = "v2:"

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _pbkdf2(password_bytes: bytes, salt: bytes) -> bytes:
    """Return the raw PBKDF2-HMAC-SHA256 digest."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt,
        _ITERATIONS,
        dklen=_HASH_BYTES,
    )


def _encode(salt: bytes, digest: bytes) -> str:
    """Encode salt + digest as a versioned v2 string."""
    return _V2_PREFIX + base64.b64encode(salt + digest).decode("utf-8")


def _decode_v2(stored: str) -> Tuple[bytes, bytes]:
    """
    Decode a v2 hash string.
    Returns (salt, digest).
    Raises ValueError on malformed input.
    """
    raw = base64.b64decode(stored[len(_V2_PREFIX):].encode("utf-8"))
    if len(raw) != _SALT_BYTES + _HASH_BYTES:
        raise ValueError("Malformed v2 hash: unexpected length.")
    return raw[:_SALT_BYTES], raw[_SALT_BYTES:]


def _decode_legacy(stored: str) -> Tuple[bytes, bytes]:
    """
    Decode a legacy (v1 SHA-256) hash string.
    Returns (salt[16], sha256_digest[32]).
    Raises ValueError on malformed input.
    """
    raw = base64.b64decode(stored.encode("utf-8"))
    if len(raw) != 16 + 32:
        raise ValueError("Malformed legacy hash: unexpected length.")
    return raw[:16], raw[16:]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """
    Hash *password* using PBKDF2-HMAC-SHA256.

    Parameters
    ----------
    password : str
        The plaintext password to hash.

    Returns
    -------
    str
        A versioned, base64-encoded hash string: "v2:<base64(salt+digest)>".

    Raises
    ------
    TypeError  : password is not a str.
    ValueError : password is empty.
    """
    if not isinstance(password, str):
        raise TypeError("Password must be a str.")
    if not password:
        raise ValueError("Password must not be empty.")

    salt   = os.urandom(_SALT_BYTES)
    digest = _pbkdf2(password.encode("utf-8"), salt)
    return _encode(salt, digest)


def verify_password(password: str, stored: str) -> bool:
    """
    Verify *password* against *stored* hash in constant time.

    Supports both v2 (PBKDF2) and legacy v1 (SHA-256) hash formats.
    Always executes a full hash operation to prevent timing-based
    enumeration, even on malformed or type-invalid inputs.

    Parameters
    ----------
    password : str
        The plaintext password to check.
    stored : str
        A hash string produced by hash_password().

    Returns
    -------
    bool
        True if and only if *password* matches *stored*.
    """
    # Dummy values ensure a hash always runs — no fast-rejection path.
    _dummy_salt   = b"\x00" * _SALT_BYTES
    _dummy_digest = _pbkdf2(b"dummy", _dummy_salt)

    if not isinstance(password, str) or not isinstance(stored, str):
        hmac.compare_digest(_dummy_digest, _dummy_digest)
        return False

    try:
        if stored.startswith(_V2_PREFIX):
            # Current path: PBKDF2-HMAC-SHA256
            salt, stored_digest = _decode_v2(stored)
            test_digest = _pbkdf2(password.encode("utf-8"), salt)
        else:
            # Legacy path: SHA-256 single-round
            salt, stored_digest = _decode_legacy(stored)
            test_digest = hashlib.sha256(
                salt + password.encode("utf-8")
            ).digest()

        return hmac.compare_digest(test_digest, stored_digest)

    except Exception:
        hmac.compare_digest(_dummy_digest, _dummy_digest)
        return False


def needs_rehash(stored: str) -> bool:
    """
    Return True if *stored* was produced by a weaker algorithm and
    should be upgraded on the next successful login.

    Parameters
    ----------
    stored : str
        A hash string to inspect.

    Returns
    -------
    bool
        True  -> legacy SHA-256 hash; call hash_password() and persist
                 the new value after verify_password() returns True.
        False -> current v2 PBKDF2 hash; no action required.
    """
    if not isinstance(stored, str):
        return False
    return not stored.startswith(_V2_PREFIX)
