@echo off
call "%~dp0run_profile_robustness_prepare.cmd" || exit /b 1
call "%~dp0run_profile_robustness_blind.cmd" || exit /b 1
call "%~dp0run_profile_robustness_reveal.cmd" || exit /b 1
