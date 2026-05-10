# Risk Battle Game A

> A terminal-based Risk-style turn strategy game written in Python —
> featuring ASCII map rendering, an event log, AI harness, and a
> Phase-3B UI augmentation layer.

[![Phase-3B Integration CI](https://github.com/YOUR_GITHUB_USERNAME/Risk_Battle_Game_A/actions/workflows/phase3_integration.yml/badge.svg)](https://github.com/YOUR_GITHUB_USERNAME/Risk_Battle_Game_A/actions/workflows/phase3_integration.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![pytest](https://img.shields.io/badge/tests-10%2F10%20passing-brightgreen)](tests/test_ui_game_loop_phase3.py)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## Table of Contents

- [Project Overview](#project-overview)
- [Repository Structure](#repository-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Running the Game](#running-the-game)
- [Running Tests](#running-tests)
- [Phase-3B Integration Package](#phase-3b-integration-package)
- [Demo Scripts](#demo-scripts)
- [CI / GitHub Actions](#ci--github-actions)
- [Commit History](#commit-history)
- [Contributing](#contributing)

---

## Project Overview

Risk Battle Game A is a turn-based strategy game played entirely in the
terminal. Players claim territories, deploy troops, attack neighbours,
and fortify positions across a classic world map rendered in ASCII art.

Key capabilities introduced in Phase 3B:

- **Safe optional imports** — all UI and rendering modules load with
  graceful fallbacks so the engine runs in minimal environments.
- **`map` command** — renders the ASCII territory map inline during play.
- **`log` command** — displays or exports the in-session event log.
- **Event logging** — every attack, reinforce, and fortify action is
  recorded to a structured event log for post-game review.

---

## Repository Structure

```
Risk_Battle_Game_A/
├── .github/
│   └── workflows/
│       └── phase3_integration.yml   # CI -- syntax check + pytest
├── ai/                              # AI player harness
├── auth/                            # Authentication utilities
├── data/                            # Game data and map definitions
├── docs/
│   ├── phase3_integration_README.md
│   └── phase3_integration_checklist.md
├── engine/                          # Core game engine
├── patches/
│   └── phase3_ui_patch.diff         # Phase-3B UI patch
├── players/                         # Player management
├── scripts/
│   ├── demo_phase3.ps1              # PowerShell smoke-test runner
│   └── demo_phase3.sh               # Bash smoke-test runner
├── tests/
│   ├── test_ui_game_loop_phase3.py  # Phase-3B unit + functional tests
│   └── ...
├── ui/
│   ├── ascii_map.py
│   ├── console.py
│   ├── game_loop.py                 # Phase-3B patched
│   └── ...
├── .gitattributes                   # LF line-ending enforcement
├── main.py
├── pytest.ini
└── README.md
```

---

## Requirements

| Dependency | Version | Notes              |
|------------|---------|--------------------|
| Python     | 3.9+    | Required           |
| pytest     | 7.0+    | Required for tests |
| flake8     | 6.0+    | Optional — lint    |

---

## Installation

```powershell
# 1. Clone the repository
git clone https://github.com/YOUR_GITHUB_USERNAME/Risk_Battle_Game_A.git
cd Risk_Battle_Game_A

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install dev dependencies
pip install pytest flake8
```

> **Windows note:** `.gitattributes` enforces LF line endings on
> `*.diff`, `*.sh`, `*.py`, `*.yml`, and `*.ini` files automatically.

---

## Running the Game

```powershell
python main.py
```

In-game commands (Phase-3B additions highlighted):

| Command      | Description                                   |
|--------------|-----------------------------------------------|
| `attack`     | Attack an adjacent territory                  |
| `reinforce`  | Deploy troops to a territory                  |
| `fortify`    | Move troops between friendly territories      |
| `map`        | **[Phase-3B]** Render the ASCII territory map |
| `log`        | **[Phase-3B]** Show event log count           |
| `log export` | **[Phase-3B]** Export log to session_log.json |
| `help`       | List all commands                             |
| `quit`       | Exit the game                                 |

---

## Running Tests

```powershell
# Phase-3B suite only
python -m pytest tests/test_ui_game_loop_phase3.py -v

# Full suite
python -m pytest --tb=short -q

# With lint
python -m flake8 ui/game_loop.py tests/test_ui_game_loop_phase3.py --max-line-length=120 --ignore=E501,W503
```

Expected Phase-3B output:

```
PASSED TestLogEventNoop::test_log_event_noop_no_event_log
PASSED TestLogEventNoop::test_log_event_noop_import_error
PASSED TestMapCommand::test_map_command_no_module
PASSED TestMapCommand::test_map_command_success
PASSED TestLogCommand::test_log_command_fallback
PASSED TestLogCommand::test_log_command_success
PASSED TestLogCommand::test_log_command_export
PASSED TestActionLogging::test_action_logging_attack
PASSED TestActionLogging::test_action_logging_reinforce
PASSED TestActionLogging::test_action_logging_fortify
10 passed
```

### Mocking strategy

| Dependency                     | Mock                                                |
|-------------------------------|-----------------------------------------------------|
| `ui.console.color_text`        | `MagicMock(side_effect=lambda text, *a, **kw: text)` |
| `ui.ascii_map.render_ascii_map`| `MagicMock(return_value="[map]")`                   |
| `engine.event_log.EventLog`    | Inline `FakeEventLog` with `.log()` and `.export_json()` |

---

## Phase-3B Integration Package

Apply the patch (first time only):

```powershell
$t = [System.IO.File]::ReadAllText('patches/phase3_ui_patch.diff')
$f = $t -replace "`r`n","`n" -replace "`r","`n"
[System.IO.File]::WriteAllText((Resolve-Path 'patches/phase3_ui_patch.diff').Path,$f,[System.Text.UTF8Encoding]::new($false))
git apply patches/phase3_ui_patch.diff
python -m py_compile ui/game_loop.py
if ($LASTEXITCODE -eq 0) { Write-Host "PASS: ui/game_loop.py" }
```

Full walkthrough: see [docs/phase3_integration_checklist.md](docs/phase3_integration_checklist.md)

---

## Demo Scripts

```powershell
# PowerShell -- minimal
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\demo_phase3.ps1

# PowerShell -- full (applies patch + entire suite)
.\scripts\demo_phase3.ps1 -Full
```

```bash
# Bash
chmod +x scripts/demo_phase3.sh && ./scripts/demo_phase3.sh --full
```

---

## CI / GitHub Actions

The workflow at `.github/workflows/phase3_integration.yml` triggers on
every push or pull request touching `ui/game_loop.py` or the Phase-3B
test file. Replace `YOUR_GITHUB_USERNAME` in the badge URL above after
pushing to GitHub.

---

## Commit History

| SHA       | Message                                                                          |
|-----------|----------------------------------------------------------------------------------|
| `8483282` | Phase 3B: UI enhancements - safe imports, map/log commands, event logging        |
| `36dc7ad` | Phase 3B: add demo scripts and CI workflow                                       |
| `64ae7c3` | chore: add .gitattributes enforcing LF line endings                              |
| HEAD      | chore: add root README with CI badge and setup instructions                      |

Tag `phase3b-integration` points to commit `8483282`.

---

## Contributing

1. Fork the repository and create a feature branch.
2. Install dev dependencies: `pip install pytest flake8`
3. Run `python -m pytest` and confirm all tests pass.
4. Open a pull request against `master` — CI runs automatically.

> **Windows contributors:** `.gitattributes` handles LF normalisation
> automatically on every `git add`.

---

*Risk Battle Game A — Phase-3B Integration Package — 2026-05-10*
