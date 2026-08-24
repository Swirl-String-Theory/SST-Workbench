@echo off
call "%~dp0run_swirl_clock_phase_discovery_prepare.cmd" || exit /b 1
call "%~dp0run_swirl_clock_phase_discovery_blind.cmd" || exit /b 1
call "%~dp0run_swirl_clock_phase_discovery_reveal.cmd" || exit /b 1
