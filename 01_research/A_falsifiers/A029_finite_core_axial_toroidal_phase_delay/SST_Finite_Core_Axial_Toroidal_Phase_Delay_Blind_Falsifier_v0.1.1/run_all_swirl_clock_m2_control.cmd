@echo off
call "%~dp0run_swirl_clock_m2_control_prepare.cmd" || exit /b 1
call "%~dp0run_swirl_clock_m2_control_blind.cmd" || exit /b 1
call "%~dp0run_swirl_clock_m2_control_reveal.cmd" || exit /b 1
