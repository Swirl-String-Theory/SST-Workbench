@echo off
setlocal
set PRESET=%1
if "%PRESET%"=="" set PRESET=basic
call run_00_setup.cmd || exit /b 1
call run_10_selftest.cmd || exit /b 1
call run_20_smoke_blind.cmd %PRESET% || exit /b 1
call run_50_package.cmd || exit /b 1
