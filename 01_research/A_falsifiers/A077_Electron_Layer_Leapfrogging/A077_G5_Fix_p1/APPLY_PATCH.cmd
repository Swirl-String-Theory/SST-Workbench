@echo off
setlocal
REM Run from the ROOT of A077-v0.1.1. The patch folder must be adjacent to it.
if defined SST_PYTHON (
  set "PY=%SST_PYTHON%"
) else if exist ".venv\Scripts\python.exe" (
  set "PY=.venv\Scripts\python.exe"
) else (
  set "PY=python"
)
"%PY%" "%~dp0apply_patch.py" --target "%CD%"
exit /b %ERRORLEVEL%
