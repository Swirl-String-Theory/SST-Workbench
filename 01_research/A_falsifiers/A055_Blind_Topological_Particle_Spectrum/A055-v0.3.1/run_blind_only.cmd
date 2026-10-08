@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=FULL"
set "WB=%~2"
if "%WB%"=="" set "WB=C:\workspace\projects\SST-Workbench"
set "SST_WORKBENCH_ROOT=%WB%"
call run_install.cmd
  if errorlevel 1 exit /b 1
call run_10_selftest.cmd
  if errorlevel 1 exit /b 1
set "PY=%~dp0..\.a055-v0.3.1-runtime\Scripts\python.exe"
"%PY%" run_instance.py FREEZE
  if errorlevel 1 exit /b 1
"%PY%" run_instance.py %MODE%
  if errorlevel 1 exit /b 1
echo A055 v0.3.1 %MODE% blind run complete; reveal not run.
