@echo off
call "%~dp0run_swirl_clock_m1_confirmatory_prepare.cmd" || exit /b 1
call "%~dp0run_swirl_clock_m1_confirmatory_blind.cmd" || exit /b 1
call "%~dp0run_swirl_clock_m1_confirmatory_reveal.cmd" || exit /b 1
