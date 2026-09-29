@echo off
call "%~dp0run_basic_prepare.cmd" || exit /b 1
call "%~dp0run_basic_blind.cmd" || exit /b 1
call "%~dp0run_basic_reveal.cmd" || exit /b 1
