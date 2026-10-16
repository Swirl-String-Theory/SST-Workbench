@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if "%~1"=="" (set "MODE=BASIC") else (set "MODE=%~1")
if not "%~2"=="" set "SST_WORKBENCH_ROOT=%~2"
if not "%~3"=="" set "SST_CROSS_CARRIER_MANIFEST=%~3"
if not exist ".venv\Scripts\python.exe" (
  call run_00_install.cmd
  if errorlevel 1 exit /b 1
)
set "PY=.venv\Scripts\python.exe"
set "PYTHONPATH=%CD%;%PYTHONPATH%"
if /I "%MODE%"=="FREEZE" goto :run
if /I "%MODE%"=="SELFTEST" goto :run
if /I "%MODE%"=="REVEAL" goto :run
if /I "%MODE%"=="REVEAL_IF_ALLOWED" goto :run
if not exist "preregistration\FROZEN_PROTOCOL.json" (
  echo [A054] No frozen protocol yet. Performing create-once FREEZE...
  "%PY%" run_instance.py FREEZE
  if errorlevel 1 exit /b 1
)
:run
"%PY%" run_instance.py %MODE%
exit /b %ERRORLEVEL%
