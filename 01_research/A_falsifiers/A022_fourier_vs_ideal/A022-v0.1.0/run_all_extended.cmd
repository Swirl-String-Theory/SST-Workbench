@echo off
setlocal
cd /d "%~dp0"
call run_00_install.cmd || exit /b 1
call run_01_build_native.cmd || exit /b 1
call run_11_prepare_all.cmd || exit /b 1
call run_30_blind_extended.cmd || exit /b 1
call run_40_reveal.cmd || exit /b 1
echo [SST-FVI] Extended campaign complete.
