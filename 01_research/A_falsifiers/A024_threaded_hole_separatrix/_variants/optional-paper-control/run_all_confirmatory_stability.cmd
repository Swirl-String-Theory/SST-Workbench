@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_00_install.cmd || exit /b 1
call run_01_build_native.cmd || exit /b 1
call run_confirmatory_stability_prepare.cmd || exit /b 1
call run_confirmatory_stability_blind.cmd || exit /b 1
call run_confirmatory_stability_reveal.cmd || exit /b 1
echo [SST-TH v0.2.1] confirmatory_stability complete.
exit /b 0
