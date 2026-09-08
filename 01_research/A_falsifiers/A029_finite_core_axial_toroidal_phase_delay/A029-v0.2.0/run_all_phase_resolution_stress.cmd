@echo off
call "%~dp0run_phase_resolution_stress_prepare.cmd" || exit /b 1
call "%~dp0run_phase_resolution_stress_blind.cmd" || exit /b 1
call "%~dp0run_phase_resolution_stress_reveal.cmd" || exit /b 1
