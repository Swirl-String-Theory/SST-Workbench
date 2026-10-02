@echo off
call "%~dp0_common.cmd" || exit /b 1
cd /d "%ROOT%"
"%PY%" -m sst_finite_core_falsifier.cli prepare --root . --config config/preset_chirality_sign.json --out outputs/chirality_sign/campaign
