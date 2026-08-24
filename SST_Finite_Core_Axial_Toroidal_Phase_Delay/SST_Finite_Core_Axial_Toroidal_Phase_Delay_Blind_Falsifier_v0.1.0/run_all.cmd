@echo off
call "%~dp0run_00_install.cmd" || exit /b 1
call "%~dp0run_01_build_native.cmd" || exit /b 1
call "%~dp0run_tests.cmd" || exit /b 1
call "%~dp0run_all_basic.cmd" || exit /b 1
