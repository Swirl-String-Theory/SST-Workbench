@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_00_install.cmd || exit /b 1
call run_01_build_native.cmd || exit /b 1
call run_density_helix_prepare.cmd || exit /b 1
call run_density_helix_blind.cmd || exit /b 1
call run_density_helix_reveal.cmd || exit /b 1
echo [SST-TH] density_helix complete. See outputs\density_helix\reveal\CONCLUSIONS.md
exit /b 0
