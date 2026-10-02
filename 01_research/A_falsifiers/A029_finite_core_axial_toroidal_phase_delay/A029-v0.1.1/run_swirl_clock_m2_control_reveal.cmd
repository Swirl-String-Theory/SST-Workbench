@echo off
call "%~dp0_common.cmd" || exit /b 1
cd /d "%ROOT%"
"%PY%" -m sst_finite_core_falsifier.cli reveal --root . --config config/preset_swirl_clock_m2_control.json --campaign outputs/swirl_clock_m2_control/campaign --blind outputs/swirl_clock_m2_control/blind --out outputs/swirl_clock_m2_control/reveal
