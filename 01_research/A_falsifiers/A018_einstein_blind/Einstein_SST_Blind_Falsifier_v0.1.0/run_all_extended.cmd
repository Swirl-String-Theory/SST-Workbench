@echo off
call "%~dp0run_00_install.cmd" || exit /b 1
call "%~dp0run_01_check_backend.cmd" || exit /b 1
call "%~dp0run_30_highres.cmd" || exit /b 1
exit /b 0
