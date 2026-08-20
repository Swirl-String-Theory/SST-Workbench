@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_00_install.cmd || exit /b 1
call run_01_build_native.cmd || exit /b 1
call run_twist_prepare.cmd || exit /b 1
call run_twist_blind.cmd || exit /b 1
call run_twist_reveal.cmd || exit /b 1
echo [SST-TH] twist complete. See outputs\twist\reveal\CONCLUSIONS.md
exit /b 0
