@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Missing .venv\Scripts\python.exe
  echo Run the normal A029 native install/build step first.
  exit /b 1
)

set "PYTHONPATH=%CD%\src;%PYTHONPATH%"

echo [A029 v0.7.0] Full preflight test suite
".venv\Scripts\python.exe" -m pytest -q tests
if errorlevel 1 exit /b %ERRORLEVEL%

echo [A029 v0.7.0] Specific-Lagrangian Mega Falsifier
".venv\Scripts\python.exe" run_specific_lagrangian_mega.py %*
set RC=%ERRORLEVEL%
if not "%RC%"=="0" exit /b %RC%

echo [DONE] A029-v0.7.0-outputs\RUN_REPORT.json
endlocal
