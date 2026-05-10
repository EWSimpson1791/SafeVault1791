# Phase-3B Integration Checklist
# Risk_Battle_Game_A — UI Augmentation Deliverables

> **Target branch:** current working branch
> **Patch file:** `patches/phase3_ui_patch.diff`
> **Primary target:** `ui/game_loop.py`

---

## Pre-flight

- [ ] Working directory is the repository root (`Risk_Battle_Game_A/`)
- [ ] Git working tree is clean (`git status` shows no uncommitted changes)
- [ ] Python ≥ 3.9 is on `PATH`
- [ ] `pytest` ≥ 7.0 is installed (`pytest --version`)
- [ ] Optional: `flake8` installed for lint checks (`flake8 --version`)

```bash
# Verify environment
python --version
pytest --version
flake8 --version || echo "flake8 not installed — lint step will be skipped"
