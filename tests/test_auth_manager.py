"""
tests/test_auth_manager.py

Full security coverage for auth/auth_manager.py.

Controls tested (6 of 6):
    1. Correct login           — success path, failure counter cleared
    2. Wrong password          — counter increments, remaining attempts shown
    3. Lockout trigger         — account locks on attempt MAX_ATTEMPTS
    4. Lockout gate            — attempt after lockout blocked before DB lookup
    5. Auto-reset after expiry — cooldown elapsed, user can log in again
    6. Dummy-hash for unknown  — unknown username still executes a hash
                                 (timing-safe: no fast rejection path)
"""

import json
import time
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os

# Make sure the project root is on sys.path when run from any directory
sys.path.insert(0, str(Path(__file__).parent.parent))

import auth.auth_manager as am
from auth.auth_manager import AuthManager, MAX_ATTEMPTS, LOCKOUT_SECONDS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_manager(tmp_path: Path) -> AuthManager:
    """Return an AuthManager backed by a temp directory."""
    store = tmp_path / "users.json"
    # Patch module-level path constants so lockout/log also land in tmp
    with patch.object(am, "LOCKOUT_STORE_PATH", tmp_path / "lockout_state.json"), \
         patch.object(am, "FAILURE_LOG_PATH",   tmp_path / "auth_failures.log"):
        manager = AuthManager(store_path=store)
    return manager, tmp_path


# ---------------------------------------------------------------------------
# Test suite
# ---------------------------------------------------------------------------

class TestAuthManagerSecurity(unittest.TestCase):

    def setUp(self):
        """Each test gets a clean isolated temp directory."""
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self.lockout_path = self.tmp / "lockout_state.json"
        self.log_path     = self.tmp / "auth_failures.log"
        self.store_path   = self.tmp / "users.json"

        # Patch module-level paths for every test
        self.patches = [
            patch.object(am, "LOCKOUT_STORE_PATH", self.lockout_path),
            patch.object(am, "FAILURE_LOG_PATH",   self.log_path),
        ]
        for p in self.patches:
            p.start()

        self.mgr = AuthManager(store_path=self.store_path)
        self.mgr.register("alice", "correct-horse-battery-staple")

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self._tmpdir.cleanup()

    # ------------------------------------------------------------------
    # 1. Correct login
    # ------------------------------------------------------------------

    def test_correct_login_returns_success(self):
        result = self.mgr.login("alice", "correct-horse-battery-staple")
        self.assertTrue(result["success"])

    def test_correct_login_clears_failure_counter(self):
        # Accumulate two failures then succeed
        self.mgr.login("alice", "wrong1")
        self.mgr.login("alice", "wrong2")
        self.mgr.login("alice", "correct-horse-battery-staple")

        # Lockout state must be absent after a successful login
        state = json.loads(self.lockout_path.read_text()) \
            if self.lockout_path.exists() else {}
        self.assertNotIn("alice", state)

    # ------------------------------------------------------------------
    # 2. Wrong password — counter and remaining-attempts message
    # ------------------------------------------------------------------

    def test_wrong_password_returns_failure(self):
        result = self.mgr.login("alice", "wrong-password")
        self.assertFalse(result["success"])
        self.assertFalse(result["locked"])

    def test_wrong_password_increments_counter(self):
        self.mgr.login("alice", "bad1")
        self.mgr.login("alice", "bad2")
        state = json.loads(self.lockout_path.read_text())
        self.assertEqual(state["alice"]["attempts"], 2)

    def test_failure_message_shows_remaining_attempts(self):
        result = self.mgr.login("alice", "bad")
        self.assertIn("remaining", result["reason"])
        # After 1 failure, should report MAX_ATTEMPTS - 1 remaining
        expected = str(MAX_ATTEMPTS - 1)
        self.assertIn(expected, result["reason"])

    # ------------------------------------------------------------------
    # 3. Lockout trigger — account locks on attempt MAX_ATTEMPTS
    # ------------------------------------------------------------------

    def test_account_locks_on_max_attempts(self):
        for _ in range(MAX_ATTEMPTS):
            self.mgr.login("alice", "wrong")

        state = json.loads(self.lockout_path.read_text())
        self.assertGreaterEqual(state["alice"]["attempts"], MAX_ATTEMPTS)
        self.assertGreater(state["alice"]["locked_at"], 0)

    def test_lockout_response_on_max_attempt(self):
        for _ in range(MAX_ATTEMPTS - 1):
            self.mgr.login("alice", "wrong")
        # Final attempt that triggers lockout
        result = self.mgr.login("alice", "wrong")
        self.assertFalse(result["success"])
        self.assertTrue(result["locked"])
        self.assertGreater(result["seconds_remaining"], 0)

    # ------------------------------------------------------------------
    # 4. Lockout gate — blocked before DB lookup
    # ------------------------------------------------------------------

    def test_locked_account_rejected_immediately(self):
        # Trigger lockout
        for _ in range(MAX_ATTEMPTS):
            self.mgr.login("alice", "wrong")

        # Even the correct password is rejected while locked
        result = self.mgr.login("alice", "correct-horse-battery-staple")
        self.assertFalse(result["success"])
        self.assertTrue(result["locked"])

    def test_locked_account_message_contains_minutes(self):
        for _ in range(MAX_ATTEMPTS):
            self.mgr.login("alice", "wrong")
        result = self.mgr.login("alice", "any")
        self.assertIn("minute", result["reason"])

    def test_failure_logged_on_locked_attempt(self):
        for _ in range(MAX_ATTEMPTS):
            self.mgr.login("alice", "wrong")
        self.mgr.login("alice", "any")
        log = self.log_path.read_text()
        self.assertIn("LOCKED_OUT", log)

    # ------------------------------------------------------------------
    # 5. Auto-reset after cooldown expiry
    # ------------------------------------------------------------------

    def test_lockout_auto_resets_after_expiry(self):
        # Trigger lockout
        for _ in range(MAX_ATTEMPTS):
            self.mgr.login("alice", "wrong")

        # Wind time forward past the lockout window
        future = time.time() + LOCKOUT_SECONDS + 1
        with patch("auth.auth_manager.time") as mock_time:
            mock_time.time.return_value = future
            locked, remaining = self.mgr.is_locked("alice")

        self.assertFalse(locked)
        self.assertEqual(remaining, 0.0)

    def test_login_succeeds_after_lockout_expiry(self):
        for _ in range(MAX_ATTEMPTS):
            self.mgr.login("alice", "wrong")

        future = time.time() + LOCKOUT_SECONDS + 1
        with patch("auth.auth_manager.time") as mock_time:
            mock_time.time.return_value = future
            result = self.mgr.login("alice", "correct-horse-battery-staple")

        self.assertTrue(result["success"])

    # ------------------------------------------------------------------
    # 6. Dummy-hash for unknown users (timing-safe path)
    # ------------------------------------------------------------------

    def test_unknown_user_returns_failure(self):
        result = self.mgr.login("ghost", "any-password")
        self.assertFalse(result["success"])

    def test_unknown_user_executes_dummy_hash(self):
        """_verify_password must be called even for non-existent users."""
        with patch("auth.auth_manager._verify_password",
                   wraps=am._verify_password) as mock_verify:
            self.mgr.login("ghost", "any-password")
            mock_verify.assert_called_once()

    def test_unknown_user_logged_as_unknown(self):
        self.mgr.login("ghost", "any-password")
        log = self.log_path.read_text()
        self.assertIn("UNKNOWN_USER", log)

    def test_unknown_user_increments_lockout_counter(self):
        for _ in range(MAX_ATTEMPTS):
            self.mgr.login("ghost", "any")
        state = json.loads(self.lockout_path.read_text())
        self.assertGreaterEqual(state["ghost"]["attempts"], MAX_ATTEMPTS)

    # ------------------------------------------------------------------
    # Admin reset
    # ------------------------------------------------------------------

    def test_admin_reset_clears_lockout(self):
        for _ in range(MAX_ATTEMPTS):
            self.mgr.login("alice", "wrong")
        self.mgr.reset_lockout("alice")
        locked, _ = self.mgr.is_locked("alice")
        self.assertFalse(locked)

    def test_register_duplicate_returns_false(self):
        self.assertFalse(self.mgr.register("alice", "new-password"))

    def test_register_new_user_returns_true(self):
        self.assertTrue(self.mgr.register("bob", "hunter2"))


if __name__ == "__main__":
    unittest.main()
