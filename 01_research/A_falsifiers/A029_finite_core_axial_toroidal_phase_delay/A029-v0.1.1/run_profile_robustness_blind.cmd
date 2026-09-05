@echo off
call "%~dp0_common.cmd" || exit /b 1
cd /d "%ROOT%"
"%PY%" -m sst_finite_core_falsifier.cli blind --root . --config config/preset_profile_robustness.json --campaign outputs/profile_robustness/campaign --out outputs/profile_robustness/blind
