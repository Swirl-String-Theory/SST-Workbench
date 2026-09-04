@echo off
call "%~dp0_common.cmd" || exit /b 1
cd /d "%ROOT%"
"%PY%" -m sst_finite_core_falsifier.cli blind --root . --config config/preset_swirl_clock_m2_diagnostic.json --campaign outputs/swirl_clock_m2_diagnostic/campaign --out outputs/swirl_clock_m2_diagnostic/blind
