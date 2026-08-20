@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_00_install.cmd || exit /b 1
call run_01_build_native.cmd || exit /b 1
call run_stability_islands_prepare.cmd || exit /b 1
call run_stability_islands_blind.cmd || exit /b 1
call run_stability_islands_reveal.cmd || exit /b 1
echo [SST-TH v0.2.0] stability_islands complete. See outputs\stability_islands\reveal\CONCLUSIONS.md
exit /b 0
