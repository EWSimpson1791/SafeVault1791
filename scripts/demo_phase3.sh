#!/usr/bin/env bash
# Phase-3B smoke-test runner (Bash)  Usage: ./scripts/demo_phase3.sh
python3 -m py_compile ui/game_loop.py && echo '[PASS] ui/game_loop.py'
python3 -m pytest tests/test_ui_game_loop_phase3.py -v && echo '[PASS] Phase-3 tests'
