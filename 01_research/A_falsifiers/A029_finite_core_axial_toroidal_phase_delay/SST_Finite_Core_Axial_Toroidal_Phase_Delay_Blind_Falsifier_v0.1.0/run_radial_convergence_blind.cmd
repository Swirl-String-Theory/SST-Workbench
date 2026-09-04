@echo off
call "%~dp0_common.cmd" || exit /b 1
cd /d "%ROOT%"
"%PY%" -m sst_finite_core_falsifier.cli blind --root . --config config/preset_radial_convergence.json --campaign outputs/radial_convergence/campaign --out outputs/radial_convergence/blind
