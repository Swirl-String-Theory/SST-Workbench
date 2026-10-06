@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set PRESET=%~1
if "%PRESET%"=="" set PRESET=basic
call run_00_install.cmd || exit /b 1
call run_05_build_cpp.cmd || exit /b 1
call run_10_selftest.cmd || exit /b 1
call run_20_blind.cmd %PRESET% || exit /b 1
call run_30_seal.cmd %PRESET% || exit /b 1
echo.
echo BLIND campaign sealed. Reveal has NOT been run.
exit /b 0
