# tests/test_dcrypt.py
"""
Unit tests for auth/dcrypt.py -- hardened PBKDF2-HMAC-SHA256 implementation.

Coverage
--------
hash_password()   : output format, salt uniqueness, type/value guards
verify_password() : v2 correct, v2 wrong, legacy v1 compat, bad inputs
needs_rehash()    : v2 detection, legacy detection, bad-type guard
Integration       : login-time migration flow (legacy -> v2 upgrade)
"""
import base64
import hashlib
import os
import pytest

from auth.dcrypt import hash_password, verify_password, needs_rehash

# ---------------------------------------------------------------------------
# Constants mirrored from dcrypt.py
# ---------------------------------------------------------------------------
_V2_PREFIX  = "v2:"
_SALT_BYTES = 32
_HASH_BYTES = 32


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _make_legacy_hash(password: str) -> str:
    """Produce a legacy v1 SHA-256 hash (16-byte salt) for compat tests."""
    salt   = os.urandom(16)
    digest = hashlib.sha256(salt + password.encode("utf-8")).digest()
    return base64.b64encode(salt + digest).decode("utf-8")


# ===========================================================================
# hash_password
# ===========================================================================

class TestHashPassword:

    def test_returns_v2_prefix(self):
        h = hash_password("hunter2")
        assert h.startswith(_V2_PREFIX), "hash must carry v2: prefix"

    def test_output_is_valid_base64(self):
        h = hash_password("hunter2")
        raw = base64.b64decode(h[len(_V2_PREFIX):].encode())
        assert isinstance(raw, bytes)

    def test_correct_byte_length(self):
        h = hash_password("hunter2")
        raw = base64.b64decode(h[len(_V2_PREFIX):].encode())
        assert len(raw) == _SALT_BYTES + _HASH_BYTES

    def test_two_calls_produce_different_hashes(self):
        # Salt is random -- identical passwords must hash differently
        assert hash_password("same") != hash_password("same")

    def test_raises_type_error_on_int(self):
        with pytest.raises(TypeError):
            hash_password(12345)

    def test_raises_type_error_on_none(self):
        with pytest.raises(TypeError):
            hash_password(None)

    def test_raises_value_error_on_empty_string(self):
        with pytest.raises(ValueError):
            hash_password("")

    def test_unicode_password(self):
        h = hash_password("passw-unicode-cafe")
        assert h.startswith(_V2_PREFIX)


# ===========================================================================
# verify_password -- v2 (PBKDF2) path
# ===========================================================================

class TestVerifyPasswordV2:

    def test_correct_password_returns_true(self):
        stored = hash_password("correct-horse")
        assert verify_password("correct-horse", stored) is True

    def test_wrong_password_returns_false(self):
        stored = hash_password("correct-horse")
        assert verify_password("wrong-horse", stored) is False

    def test_empty_password_returns_false(self):
        stored = hash_password("correct-horse")
        assert verify_password("", stored) is False

    def test_non_str_password_returns_false(self):
        stored = hash_password("correct-horse")
        assert verify_password(None, stored) is False

    def test_non_str_stored_returns_false(self):
        assert verify_password("correct-horse", 42) is False

    def test_corrupted_stored_returns_false(self):
        assert verify_password("correct-horse", "v2:!!!notbase64!!!") is False

    def test_wrong_length_stored_returns_false(self):
        short = _V2_PREFIX + base64.b64encode(b"tooshort").decode()
        assert verify_password("x", short) is False


# ===========================================================================
# verify_password -- legacy v1 (SHA-256) path
# ===========================================================================

class TestVerifyPasswordLegacy:

    def test_correct_password_legacy_hash_returns_true(self):
        # Legacy v1 SHA-256 hashes must still verify correctly
        stored = _make_legacy_hash("legacy-password")
        assert verify_password("legacy-password", stored) is True

    def test_wrong_password_legacy_hash_returns_false(self):
        stored = _make_legacy_hash("legacy-password")
        assert verify_password("wrong-password", stored) is False

    def test_corrupted_legacy_stored_returns_false(self):
        assert verify_password("x", "notvalidbase64!!!") is False


# ===========================================================================
# needs_rehash
# ===========================================================================

class TestNeedsRehash:

    def test_v2_hash_does_not_need_rehash(self):
        stored = hash_password("secure-pass")
        assert needs_rehash(stored) is False

    def test_legacy_hash_needs_rehash(self):
        stored = _make_legacy_hash("old-pass")
        assert needs_rehash(stored) is True

    def test_none_returns_false(self):
        assert needs_rehash(None) is False

    def test_int_returns_false(self):
        assert needs_rehash(42) is False

    def test_empty_string_needs_rehash(self):
        # No v2: prefix -- treated as legacy
        assert needs_rehash("") is True


# ===========================================================================
# Integration -- login-time migration flow
# ===========================================================================

class TestRehashMigrationFlow:

    def test_legacy_to_v2_upgrade_flow(self):
        """
        Full migration flow:
        1. Start with a legacy SHA-256 hash.
        2. verify_password succeeds.
        3. needs_rehash detects it as legacy.
        4. Re-hash produces a v2 hash.
        5. New v2 hash verifies correctly.
        6. needs_rehash returns False on the v2 hash.
        """
        password = "migrate-me"
        legacy   = _make_legacy_hash(password)

        assert verify_password(password, legacy)  is True
        assert needs_rehash(legacy)               is True

        upgraded = hash_password(password)
        assert upgraded.startswith(_V2_PREFIX)
        assert verify_password(password, upgraded) is True
        assert needs_rehash(upgraded)              is False
