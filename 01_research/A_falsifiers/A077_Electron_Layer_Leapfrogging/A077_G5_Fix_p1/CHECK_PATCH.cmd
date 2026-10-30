@echo off
setlocal
if defined SST_PYTHON (
  set "PY=%SST_PYTHON%"
) else if exist ".venv\Scripts\python.exe" (
  set "PY=.venv\Scripts\python.exe"
) else (
  set "PY=python"
)
"%PY%" "%~dp0apply_patch.py" --target "%CD%" --check
exit /b %ERRORLEVEL%
