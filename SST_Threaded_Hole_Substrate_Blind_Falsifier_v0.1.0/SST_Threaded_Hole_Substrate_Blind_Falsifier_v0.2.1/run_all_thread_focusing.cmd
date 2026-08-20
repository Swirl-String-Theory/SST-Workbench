@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_00_install.cmd || exit /b 1
call run_01_build_native.cmd || exit /b 1
call run_thread_focusing_prepare.cmd || exit /b 1
call run_thread_focusing_blind.cmd || exit /b 1
call run_thread_focusing_reveal.cmd || exit /b 1
echo [SST-TH v0.2.1] thread_focusing complete.
exit /b 0
