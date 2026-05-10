# Phase-3B smoke-test runner (PowerShell)  Usage: .\scripts\demo_phase3.ps1 [-Full]
param([switch]$Full)
python -m py_compile ui\game_loop.py; if ($LASTEXITCODE -eq 0) { Write-Host '[PASS] ui/game_loop.py' } else { Write-Host '[FAIL] ui/game_loop.py' }
python -m pytest tests\test_ui_game_loop_phase3.py -v; if ($LASTEXITCODE -eq 0) { Write-Host '[PASS] Phase-3 tests 10/10' } else { Write-Host '[FAIL] Phase-3 tests' }
