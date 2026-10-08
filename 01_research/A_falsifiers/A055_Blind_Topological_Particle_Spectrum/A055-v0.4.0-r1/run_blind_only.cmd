@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=FULL"
set "WB=%~2"
if "%WB%"=="" set "WB=C:\workspace\projects\SST-Workbench"
set "SST_WORKBENCH_ROOT=%WB%"
call run_install.cmd || exit /b 1
call run_10_selftest.cmd || exit /b 1
set "PY=.venv\Scripts\python.exe"
%PY% run_instance.py FREEZE || exit /b 1
%PY% run_instance.py %MODE% || exit /b 1
echo A055 v0.4.0 %MODE% blind run complete; reveal not run.
