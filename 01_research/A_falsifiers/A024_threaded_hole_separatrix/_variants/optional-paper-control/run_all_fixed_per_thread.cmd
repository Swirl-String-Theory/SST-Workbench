@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_00_install.cmd || exit /b 1
call run_01_build_native.cmd || exit /b 1
call run_fixed_per_thread_prepare.cmd || exit /b 1
call run_fixed_per_thread_blind.cmd || exit /b 1
call run_fixed_per_thread_reveal.cmd || exit /b 1
echo [SST-TH v0.2.1] fixed_per_thread complete.
exit /b 0
