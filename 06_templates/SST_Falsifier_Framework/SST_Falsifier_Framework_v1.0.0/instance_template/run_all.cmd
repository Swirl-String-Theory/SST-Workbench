@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (set "MODE=BASIC") else (set "MODE=%~1")
if not defined SST_FALSIFIER_FRAMEWORK_ROOT set "SST_FALSIFIER_FRAMEWORK_ROOT=%~dp0..\..\..\..\04_tools\D_proof\SST_Falsifier_Framework_v1.0.0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")
%PY% run_instance.py %MODE%
exit /b %ERRORLEVEL%
