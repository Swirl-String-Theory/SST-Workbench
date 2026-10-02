@echo off
call "%~dp0run_00_install.cmd" || exit /b 1
call "%~dp0run_01_check_backend.cmd" || exit /b 1
call "%~dp0run_20_standard.cmd" || exit /b 1
exit /b 0
