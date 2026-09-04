@echo off
call "%~dp0_common.cmd" || exit /b 1
cd /d "%ROOT%"
"%PY%" -m sst_finite_core_falsifier.cli blind --root . --config config/preset_basic.json --campaign outputs/basic/campaign --out outputs/basic/blind
