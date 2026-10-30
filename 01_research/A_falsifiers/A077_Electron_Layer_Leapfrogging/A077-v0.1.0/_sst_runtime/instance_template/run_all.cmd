@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (set "MODE=BASIC") else (set "MODE=%~1")
if defined SST_PYTHON (set "PY=%SST_PYTHON%") else if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")
set "PYTHONPATH=%CD%;%PYTHONPATH%"
"%PY%" -u progress_supervisor.py "%MODE%"
exit /b %ERRORLEVEL%
