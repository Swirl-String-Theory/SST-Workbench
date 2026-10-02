@echo off
setlocal
cd /d "%~dp0"
call run_00_install.cmd || exit /b 1
call run_01_build_native.cmd
call run_12_prepare_relaxed_control.cmd || exit /b 1
call run_31_blind_relaxed_control.cmd || exit /b 1
call run_40_reveal.cmd || exit /b 1
echo [SST-FVI] Ideal + relaxed-control campaign complete.
