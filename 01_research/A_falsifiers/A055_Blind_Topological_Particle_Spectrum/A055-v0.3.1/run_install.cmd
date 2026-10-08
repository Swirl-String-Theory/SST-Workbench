@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0..\.a055-v0.3.1-runtime\Scripts\python.exe" (
  py -3 -m venv "%~dp0..\.a055-v0.3.1-runtime" 2>nul || python -m venv "%~dp0..\.a055-v0.3.1-runtime"
  if errorlevel 1 exit /b 1
)
set "PY=%~dp0..\.a055-v0.3.1-runtime\Scripts\python.exe"
"%PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b %ERRORLEVEL%
"%PY%" -m pip install -r requirements.txt
exit /b %ERRORLEVEL%
