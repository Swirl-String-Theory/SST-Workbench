@echo off
setlocal
cd /d "%~dp0"
set PRESET=%1
if "%PRESET%"=="" set PRESET=basic
call run_install.cmd || exit /b 1
call run_02_backend_selftest.cmd || exit /b 1
call run_10_framework_selftest.cmd || exit /b 1
call run_20_smoke_blind.cmd %PRESET% || exit /b 1
call run_30_smoke_reveal.cmd || exit /b 1
call run_40_report.cmd || exit /b 1
call run_50_package.cmd || exit /b 1
echo PASS - A056 v0.2.1 SST Framework v1.0.2 integration smoke complete.
