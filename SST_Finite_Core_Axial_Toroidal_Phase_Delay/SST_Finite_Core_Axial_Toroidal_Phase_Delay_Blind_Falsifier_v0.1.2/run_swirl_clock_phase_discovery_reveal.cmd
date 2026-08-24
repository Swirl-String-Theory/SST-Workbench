@echo off
call "%~dp0_common.cmd" || exit /b 1
cd /d "%ROOT%"
"%PY%" -m sst_finite_core_falsifier.cli reveal --root . --config config/preset_swirl_clock_phase_discovery.json --campaign outputs/swirl_clock_phase_discovery/campaign --blind outputs/swirl_clock_phase_discovery/blind --out outputs/swirl_clock_phase_discovery/reveal
