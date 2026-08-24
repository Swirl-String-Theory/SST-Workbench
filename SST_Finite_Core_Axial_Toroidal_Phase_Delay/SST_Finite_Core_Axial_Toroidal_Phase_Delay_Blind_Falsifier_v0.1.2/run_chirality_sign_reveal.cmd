@echo off
call "%~dp0_common.cmd" || exit /b 1
cd /d "%ROOT%"
"%PY%" -m sst_finite_core_falsifier.cli reveal --root . --config config/preset_chirality_sign.json --campaign outputs/chirality_sign/campaign --blind outputs/chirality_sign/blind --out outputs/chirality_sign/reveal
