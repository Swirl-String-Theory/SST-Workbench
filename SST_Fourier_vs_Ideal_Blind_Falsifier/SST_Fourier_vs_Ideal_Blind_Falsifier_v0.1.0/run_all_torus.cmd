@echo off
setlocal
cd /d "%~dp0"
call run_00_install.cmd || exit /b 1
call run_01_build_native.cmd
call run_10_prepare_torus.cmd || exit /b 1
call run_20_blind_torus.cmd || exit /b 1
call run_40_reveal.cmd || exit /b 1
echo [SST-FVI] Complete. Blind scoring was sealed before source identity reveal.
