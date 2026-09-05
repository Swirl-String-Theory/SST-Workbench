@echo off
call "%~dp0_common.cmd" || exit /b 1
cd /d "%ROOT%"
"%PY%" -m sst_finite_core_falsifier.cli reveal --root . --config config/preset_core_radius.json --campaign outputs/core_radius/campaign --blind outputs/core_radius/blind --out outputs/core_radius/reveal
