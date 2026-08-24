@echo off
call "%~dp0run_core_radius_prepare.cmd" || exit /b 1
call "%~dp0run_core_radius_blind.cmd" || exit /b 1
call "%~dp0run_core_radius_reveal.cmd" || exit /b 1
