@echo off
call "%~dp0_common.cmd" || exit /b 1
cd /d "%ROOT%"
"%PY%" -m sst_finite_core_falsifier.cli prepare --root . --config config/preset_swirl_clock_m1_confirmatory.json --out outputs/swirl_clock_m1_confirmatory/campaign
