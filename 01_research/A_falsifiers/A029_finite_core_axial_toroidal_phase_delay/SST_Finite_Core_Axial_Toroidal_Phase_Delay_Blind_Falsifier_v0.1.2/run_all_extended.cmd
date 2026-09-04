@echo off
call "%~dp0run_extended_prepare.cmd" || exit /b 1
call "%~dp0run_extended_blind.cmd" || exit /b 1
call "%~dp0run_extended_reveal.cmd" || exit /b 1
