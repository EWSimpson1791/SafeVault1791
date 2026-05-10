# auth/dcrypt.py

import hashlib
import os
import base64


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256 + random salt.
    Returns a base64-encoded string: salt + hash.
    """
    if not isinstance(password, str):
        raise TypeError("Password must be a string.")

    salt = os.urandom(16)  # 128-bit salt
    pwd_bytes = password.encode("utf-8")

    hash_bytes = hashlib.sha256(salt + pwd_bytes).digest()

    # Store salt + hash together
    combined = salt + hash_bytes
    return base64.b64encode(combined).decode("utf-8")


def verify_password(password: str, stored: str) -> bool:
    """
    Verify a password against a stored base64(salt+hash).
    """
    try:
        combined = base64.b64decode(stored.encode("utf-8"))
        salt = combined[:16]
        stored_hash = combined[16:]

        pwd_bytes = password.encode("utf-8")
        test_hash = hashlib.sha256(salt + pwd_bytes).digest()

        return test_hash == stored_hash

    except Exception:
        return False
