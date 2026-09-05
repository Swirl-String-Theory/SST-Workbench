@echo off
call "%~dp0run_swirl_clock_m2_diagnostic_prepare.cmd" || exit /b 1
call "%~dp0run_swirl_clock_m2_diagnostic_blind.cmd" || exit /b 1
call "%~dp0run_swirl_clock_m2_diagnostic_reveal.cmd" || exit /b 1
