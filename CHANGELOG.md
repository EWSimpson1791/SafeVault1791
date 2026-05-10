python -c "
content = open('CHANGELOG.md', 'w', newline='\n')
content.write('''# Changelog

All notable changes to Risk Battle Game A are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

---

## [Phase 3B] - 2026-05-10

### Added — Full Source Codebase (9093889)
- `engine/` — complete game engine package
  - `actions/` — attack, fortify, reinforce action modules
  - `attack/` — attack phase orchestration
  - `fortify/` — fortification phase orchestration
  - `reinforcement/` — reinforcement calculation and phase runner
  - `setup/` — game initializer
  - `loop/` — game loop runner
  - `turn/` — turn manager
  - `game_rules.py`, `game_state.py`, `game_initializer.py`
- `ui/` — full UI package with corrected `__init__.py`
  - `ascii_map.py` — ASCII territory map renderer
  - `console.py` — terminal colour utilities
  - `event_log.py` — session event log writer
  - `game_shell.py` — interactive game shell
  - `html.py` — HTML output renderer
  - `player_setup.py` — player configuration UI
  - `status.py` — status display utilities
- `ai/` — AI player harness (`ai_game_loop.py`, `decision.py`, `decision_example.py`)
- `auth/` — authentication layer (`auth_manager.py`, `cli.py`, `dcrypt.py`, `user_store.py`)
- `console/` — standalone console package
- `data/` — map and territory data (`risk_map.json`, `map_loader.py`, `territories_data.py`)
- `players/` — player management (`player_manager.py`)
- `main.py` and `main/` — dual entry points
- `validate_map.py` — map integrity validator
- `pytest.ini` — pytest configuration
- `scripts/demo_ui.py` — UI smoke-test demo script
- `tests/` — ten additional test modules covering auth, data, event log,
  game rules, main, players, reinforcement, setup, and UI rendering
- `.github/workflows/ci.yml` — secondary CI workflow

### Added — Repository Hygiene
- `.gitignore` (c95fb4b) — filters Python (`__pycache__/`, `*.pyc`, `.venv/`),
  Windows (`Thumbs.db`, `Desktop.ini`), Office recovery files (`*.docx`, `~$*`),
  project-specific noise (`session_log.json`, `pytest.ini.py`)
- `.gitattributes` (64ae7c3) — enforces LF line endings on `*.py`, `*.sh`,
  `*.yml`, `*.diff`, `*.patch`, `*.md`, `*.ini`, `*.cfg`, `*.toml`, `*.ps1`;
  marks binary assets (`*.png`, `*.jpg`, `*.zip`, `*.exe`) as binary

### Added — Documentation
- `README.md` (619ea88) — root README with project overview, repository
  structure, installation guide, in-game command reference, test instructions,
  Phase-3B patch walkthrough, demo script usage, and CI badge

### Added — Phase 3B UI Augmentation (8483282, tag: phase3b-integration)
- Safe optional imports in `ui/game_loop.py` — all rendering and logging
  modules load with graceful `ImportError` fallbacks; engine runs in
  minimal environments with no hard UI dependency
- `map` command — renders the ASCII territory map inline during play via
  `ui.ascii_map.render_ascii_map`
- `log` command — prints current in-session event log entry count
- `log export` command — exports the full session log to `session_log.json`
- Structured event logging — every `attack`, `reinforce`, and `fortify`
  action is recorded to `engine.event_log.EventLog` with timestamp,
  action type, and territory metadata

### Added — CI / Demo (36dc7ad)
- `.github/workflows/phase3_integration.yml` — GitHub Actions workflow
  triggering on pushes to `ui/game_loop.py` and the Phase-3B test file;
  runs on Python 3.11; steps: syntax check (`py_compile`) + `pytest`
- `scripts/demo_phase3.ps1` — PowerShell smoke-test runner with optional
  `-Full` flag to apply the patch and run the entire test suite
- `scripts/demo_phase3.sh` — Bash equivalent for Linux / macOS / WSL;
  supports `--full` flag; exits `0` on success, `1` on any failure

### Added — Phase 3B Test Suite (8483282)
- `tests/test_ui_game_loop_phase3.py` — 10/10 unit and functional tests
  covering all Phase-3B code paths with full in-process mocking:
  - `TestLogEventNoop` — no-op behaviour when `EventLog` is absent or
    raises `ImportError`
  - `TestMapCommand` — ASCII map render with and without `ascii_map` module
  - `TestLogCommand` — log count display, fallback, and `log export` path
  - `TestActionLogging` — event recording for attack, reinforce, and fortify

### Fixed
- `ui/__init.py` renamed to `ui/__init__.py` (877979c → squashed into
  9093889) — corrected missing double underscore; Python now correctly
  recognises `ui` as an importable package

---

## [Phase 3A] - Prior to 2026-05-10

> Phase 3A established the base game engine, territory model, player
> management, and initial UI shell. Commits predating the Phase-3B
> integration tag (`phase3b-integration` → 8483282) are not individually
> listed here. See `git log 8483282` for the full pre-3B history.

---

## Legend

| Prefix | Meaning |
|--------|---------|
| `feat` | New feature or capability |
| `chore` | Build, config, or housekeeping change with no functional impact |
| `fix` | Bug or defect correction |
| `docs` | Documentation only |
| `test` | Test additions or corrections |
| `refactor` | Code restructuring with no behaviour change |

---

*Risk Battle Game A — maintained by EWSimpson1791*
*Repository: https://github.com/EWSimpson1791/SafeVault1791*
''')
content.close()
print('DONE: CHANGELOG.md created')