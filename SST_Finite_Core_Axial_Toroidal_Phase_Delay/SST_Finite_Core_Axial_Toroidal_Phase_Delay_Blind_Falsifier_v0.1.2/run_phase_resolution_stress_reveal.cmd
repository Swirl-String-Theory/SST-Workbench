@echo off
call "%~dp0_common.cmd" || exit /b 1
cd /d "%ROOT%"
"%PY%" -m sst_finite_core_falsifier.cli reveal --root . --config config/preset_phase_resolution_stress.json --campaign outputs/phase_resolution_stress/campaign --blind outputs/phase_resolution_stress/blind --out outputs/phase_resolution_stress/reveal
