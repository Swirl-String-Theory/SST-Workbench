@echo off
setlocal
cd /d "%~dp0"
call .venv\Scripts\activate.bat
set PYTHONPATH=%CD%

if not exist "private\reveal_key.json" (
  echo ERROR: private\reveal_key.json is missing.
  echo The blind prepare stage must have completed first.
  exit /b 1
)

if not exist "reveal\reveal_target.json" (
  echo ERROR: reveal\reveal_target.json is missing.
  echo Extract the separate v0.2.0 REVEAL_KEY archive only after BLIND sealing.
  exit /b 1
)

python -m sst_qgi.cli reveal --config configs\extended.json
if errorlevel 1 exit /b 1

python -m sst_qgi.cli package --config configs\extended.json
if errorlevel 1 exit /b 1

echo.
echo Reveal complete.
endlocal
