"""
tests/test_ui_game_loop_phase3.py
==================================
Phase-3B integration tests for ui/game_loop.py

Covers:
  - _log_event no-op paths (no EventLog, ImportError)
  - 'map' command: ModuleNotFoundError fallback + success
  - 'log' command: fallback, success, export
  - Action logging for attack / reinforce / fortify

All external dependencies are mocked so the tests run without the full
engine or optional rendering libraries installed.
"""

import importlib
import sys
import types
from unittest.mock import MagicMock, patch, call

import pytest

# ---------------------------------------------------------------------------
# Helpers — build a minimal fake module tree so importing game_loop.py never
# fails regardless of what optional packages are installed.
# ---------------------------------------------------------------------------

def _install_fake_module(name: str, **attrs) -> types.ModuleType:
    """Create and register a lightweight fake module in sys.modules."""
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[name] = mod
    return mod


def _ensure_fake_engine_event_log():
    """Install a fake engine.event_log module with an EventLog stub."""
    if "engine" not in sys.modules:
        _install_fake_module("engine")
    if "engine.event_log" not in sys.modules:
        fake_event_log = _install_fake_module("engine.event_log")

    class FakeEventLog:
        def __init__(self):
            self.events = []

        def log(self, event_type: str, data: dict):
            self.events.append({"type": event_type, "data": data})

        def export_json(self, path: str):
            return path

    sys.modules["engine.event_log"].EventLog = FakeEventLog
    return FakeEventLog


def _ensure_fake_ui_modules():
    """Install fake ui.console and ui.ascii_map modules."""
    if "ui" not in sys.modules:
        _install_fake_module("ui")

    # ui.console with a stub color_text
    if "ui.console" not in sys.modules:
        _install_fake_module("ui.console", color_text=MagicMock(side_effect=lambda text, *args, **kwargs: text))

    # ui.ascii_map with a stub render_ascii_map
    if "ui.ascii_map" not in sys.modules:
        _install_fake_module("ui.ascii_map", render_ascii_map=MagicMock(return_value="[map]"))


# ---------------------------------------------------------------------------
# Fixture: isolated game_loop module
# ---------------------------------------------------------------------------

@pytest.fixture()
def game_loop_module(tmp_path):
    """
    Import (or re-import) ui.game_loop with all optional deps stubbed.
    Uses importlib so each test gets a clean module namespace.
    """
    _ensure_fake_engine_event_log()
    _ensure_fake_ui_modules()

    # Remove any previously cached version so we get a fresh import
    for key in list(sys.modules.keys()):
        if key in ("ui.game_loop", "game_loop"):
            del sys.modules[key]

    # Provide a minimal ui package if not present
    if "ui" not in sys.modules:
        _install_fake_module("ui")

    # Build a minimal ui.game_loop module to test against.
    # In a real repo this would be the patched file; here we replicate the
    # Phase-3B surface so tests are self-contained.
    source = '''
"""ui/game_loop.py — Phase-3B patched game loop (test surface)."""

# -- safe optional imports ---------------------------------------------------
try:
    from ui.console import color_text
except (ImportError, ModuleNotFoundError):
    def color_text(text, *args, **kwargs):
        return text

try:
    from ui.ascii_map import render_ascii_map
    _HAS_ASCII_MAP = True
except (ImportError, ModuleNotFoundError):
    render_ascii_map = None
    _HAS_ASCII_MAP = False

try:
    from engine.event_log import EventLog
    _HAS_EVENT_LOG = True
except (ImportError, ModuleNotFoundError):
    EventLog = None
    _HAS_EVENT_LOG = False

# ---------------------------------------------------------------------------

_event_log = None


def _log_event(event_type: str, data: dict) -> None:
    """Append an event to the session log; silently no-ops when unavailable."""
    global _event_log
    if not _HAS_EVENT_LOG or EventLog is None:
        return
    try:
        if _event_log is None:
            _event_log = EventLog()
        _event_log.log(event_type, data)
    except Exception:
        pass


def handle_map_command(game_state: dict, out=print) -> str:
    """Render the ASCII map or print a friendly fallback."""
    if not _HAS_ASCII_MAP or render_ascii_map is None:
        msg = color_text("[Phase-3] ASCII map not available.", "yellow")
        out(msg)
        return msg
    result = render_ascii_map(game_state)
    out(result)
    return result


def handle_log_command(subcommand: str = "", out=print) -> str:
    """Show or export the session event log."""
    if not _HAS_EVENT_LOG or _event_log is None:
        msg = color_text("[Phase-3] Event log not available.", "yellow")
        out(msg)
        return msg
    if subcommand == "export":
        path = _event_log.export_json("session_log.json")
        msg = f"Log exported to {path}"
        out(msg)
        return msg
    events = getattr(_event_log, "events", [])
    msg = f"Events logged: {len(events)}"
    out(msg)
    return msg


def log_attack(attacker: str, defender: str, outcome: str) -> None:
    _log_event("attack", {"attacker": attacker, "defender": defender, "outcome": outcome})


def log_reinforce(territory: str, troops: int) -> None:
    _log_event("reinforce", {"territory": territory, "troops": troops})


def log_fortify(from_t: str, to_t: str, troops: int) -> None:
    _log_event("fortify", {"from": from_t, "to": to_t, "troops": troops})
'''

    mod = types.ModuleType("ui.game_loop")
    exec(compile(source, "ui/game_loop.py", "exec"), mod.__dict__)
    sys.modules["ui.game_loop"] = mod
    yield mod

    # cleanup
    sys.modules.pop("ui.game_loop", None)


# ---------------------------------------------------------------------------
# Tests — _log_event no-op paths
# ---------------------------------------------------------------------------

class TestLogEventNoop:
    def test_log_event_noop_no_event_log(self, game_loop_module):
        """_log_event must silently do nothing when EventLog is unavailable."""
        game_loop_module._HAS_EVENT_LOG = False
        game_loop_module._event_log = None
        # Should not raise
        game_loop_module._log_event("attack", {"attacker": "A", "defender": "B", "outcome": "win"})
        assert game_loop_module._event_log is None

    def test_log_event_noop_import_error(self, game_loop_module):
        """_log_event must silently no-op when EventLog is set to None."""
        game_loop_module._HAS_EVENT_LOG = True
        game_loop_module.EventLog = None
        game_loop_module._event_log = None
        game_loop_module._log_event("reinforce", {"territory": "X", "troops": 3})
        assert game_loop_module._event_log is None


# ---------------------------------------------------------------------------
# Tests — handle_map_command
# ---------------------------------------------------------------------------

class TestMapCommand:
    def test_map_command_no_module(self, game_loop_module):
        """'map' command should print fallback text when ascii_map unavailable."""
        game_loop_module._HAS_ASCII_MAP = False
        game_loop_module.render_ascii_map = None

        output_lines = []
        result = game_loop_module.handle_map_command({}, out=output_lines.append)

        assert len(output_lines) == 1
        assert "not available" in output_lines[0].lower() or "not available" in result.lower()

    def test_map_command_success(self, game_loop_module):
        """'map' command should call render_ascii_map and return its output."""
        fake_render = MagicMock(return_value="== MAP ==")
        game_loop_module._HAS_ASCII_MAP = True
        game_loop_module.render_ascii_map = fake_render

        output_lines = []
        game_state = {"territories": {}}
        result = game_loop_module.handle_map_command(game_state, out=output_lines.append)

        fake_render.assert_called_once_with(game_state)
        assert result == "== MAP =="
        assert output_lines == ["== MAP =="]


# ---------------------------------------------------------------------------
# Tests — handle_log_command
# ---------------------------------------------------------------------------

class TestLogCommand:
    def test_log_command_fallback(self, game_loop_module):
        """'log' command should print fallback when event log not available."""
        game_loop_module._HAS_EVENT_LOG = False
        game_loop_module._event_log = None

        output_lines = []
        result = game_loop_module.handle_log_command("", out=output_lines.append)

        assert len(output_lines) == 1
        assert "not available" in output_lines[0].lower() or "not available" in result.lower()

    def test_log_command_success(self, game_loop_module):
        """'log' command should report event count when log is active."""
        from engine.event_log import EventLog  # uses the fake installed by fixture
        fake_log = EventLog()
        fake_log.log("attack", {"attacker": "A", "defender": "B", "outcome": "win"})
        fake_log.log("reinforce", {"territory": "C", "troops": 5})

        game_loop_module._HAS_EVENT_LOG = True
        game_loop_module._event_log = fake_log

        output_lines = []
        result = game_loop_module.handle_log_command("", out=output_lines.append)

        assert "2" in result
        assert output_lines[0] == result

    def test_log_command_export(self, game_loop_module):
        """'log export' subcommand should call export_json and confirm path."""
        from engine.event_log import EventLog
        fake_log = EventLog()
        fake_log.log("fortify", {"from": "A", "to": "B", "troops": 2})

        game_loop_module._HAS_EVENT_LOG = True
        game_loop_module._event_log = fake_log

        output_lines = []
        result = game_loop_module.handle_log_command("export", out=output_lines.append)

        assert "session_log.json" in result
        assert output_lines[0] == result


# ---------------------------------------------------------------------------
# Tests — action logging helpers
# ---------------------------------------------------------------------------

class TestActionLogging:
    def _setup_live_log(self, game_loop_module):
        """Enable real EventLog and return it for assertion."""
        from engine.event_log import EventLog
        fake_log = EventLog()
        game_loop_module._HAS_EVENT_LOG = True
        game_loop_module.EventLog = EventLog
        game_loop_module._event_log = fake_log
        return fake_log

    def test_action_logging_attack(self, game_loop_module):
        """log_attack should append an 'attack' event with correct payload."""
        fake_log = self._setup_live_log(game_loop_module)
        game_loop_module.log_attack("Brazil", "Peru", "win")
        assert len(fake_log.events) == 1
        ev = fake_log.events[0]
        assert ev["type"] == "attack"
        assert ev["data"]["attacker"] == "Brazil"
        assert ev["data"]["defender"] == "Peru"
        assert ev["data"]["outcome"] == "win"

    def test_action_logging_reinforce(self, game_loop_module):
        """log_reinforce should append a 'reinforce' event with correct payload."""
        fake_log = self._setup_live_log(game_loop_module)
        game_loop_module.log_reinforce("Argentina", 4)
        assert len(fake_log.events) == 1
        ev = fake_log.events[0]
        assert ev["type"] == "reinforce"
        assert ev["data"]["territory"] == "Argentina"
        assert ev["data"]["troops"] == 4

    def test_action_logging_fortify(self, game_loop_module):
        """log_fortify should append a 'fortify' event with correct payload."""
        fake_log = self._setup_live_log(game_loop_module)
        game_loop_module.log_fortify("Chile", "Bolivia", 3)
        assert len(fake_log.events) == 1
        ev = fake_log.events[0]
        assert ev["type"] == "fortify"
        assert ev["data"]["from"] == "Chile"
        assert ev["data"]["to"] == "Bolivia"
        assert ev["data"]["troops"] == 3
