@echo off
call "%~dp0_common.cmd" || exit /b 1
cd /d "%ROOT%"
"%PY%" -m sst_finite_core_falsifier.cli reveal --root . --config config/preset_extended.json --campaign outputs/extended/campaign --blind outputs/extended/blind --out outputs/extended/reveal
