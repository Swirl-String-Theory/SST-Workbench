@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")
rem Keep the instance root importable while run_python.py enforces the shared-framework pin.
set "PYTHONPATH=%CD%;%PYTHONPATH%"
"%PY%" run_python.py %*
exit /b %ERRORLEVEL%
