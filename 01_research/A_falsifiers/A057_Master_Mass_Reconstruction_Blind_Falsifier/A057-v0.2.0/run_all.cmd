@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (set "MODE=BASIC") else (set "MODE=%~1")
if not "%~2"=="" set "SST_WORKBENCH_ROOT=%~2"
if not "%~3"=="" set "SST_CROSS_CARRIER_MANIFEST=%~3"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")
set "PYTHONPATH=%CD%;%PYTHONPATH%"
%PY% run_instance.py %MODE%
exit /b %ERRORLEVEL%
