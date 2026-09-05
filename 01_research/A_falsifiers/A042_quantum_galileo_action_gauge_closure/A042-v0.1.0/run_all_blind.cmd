@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo SST Quantum Galileo Action-Gauge Closure Falsifier v0.1.0
echo BLIND chain
echo ============================================================
call run_01_install.cmd
if errorlevel 1 exit /b 1
call run_02_build_native.cmd
if errorlevel 1 exit /b 1
call run_03_tests.cmd
if errorlevel 1 exit /b 1
call run_prepare_blind.cmd
if errorlevel 1 exit /b 1
call run_basic.cmd
if errorlevel 1 exit /b 1
call run_extended.cmd
if errorlevel 1 exit /b 1
call run_package.cmd
if errorlevel 1 exit /b 1
echo.
echo BLIND run complete. Do not share private\reveal_key.json.
endlocal
