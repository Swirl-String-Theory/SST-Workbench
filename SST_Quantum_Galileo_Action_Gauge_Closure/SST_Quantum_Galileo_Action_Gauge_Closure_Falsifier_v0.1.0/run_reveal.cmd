@echo off
setlocal
cd /d "%~dp0"
call .venv\Scripts\activate.bat
set PYTHONPATH=%CD%
if not exist "private\reveal_key.json" (
  echo ERROR: private\reveal_key.json is missing. Reveal is impossible.
  exit /b 1
)
python -m sst_qgi.cli reveal --config configs\extended.json
if errorlevel 1 exit /b 1
python -m sst_qgi.cli package --config configs\extended.json
if errorlevel 1 exit /b 1
endlocal
