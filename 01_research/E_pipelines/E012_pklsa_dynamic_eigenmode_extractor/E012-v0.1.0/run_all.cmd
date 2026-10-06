@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "WB="
set "PRESET=quick"
set "FORCEPY="

:parse
if "%~1"=="" goto parsed
if /I "%~1"=="--preset" (
  set "PRESET=%~2"
  shift
  shift
  goto parse
)
if /I "%~1"=="--force-python" (
  set "FORCEPY=--force-python"
  shift
  goto parse
)
if not defined WB (
  set "WB=%~1"
  shift
  goto parse
)
echo [E012] Unknown argument: %~1
exit /b 2

:parsed
if not exist ".venv\Scripts\python.exe" (
  echo [E012] Creating virtual environment...
  py -3 -m venv .venv
  if errorlevel 1 exit /b 10
)

set "PY=.venv\Scripts\python.exe"
"%PY%" -m pip install --upgrade pip
if errorlevel 1 exit /b 11
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 exit /b 12

echo [E012] Running tests...
"%PY%" -m pytest -q
if errorlevel 1 exit /b 20

set "WBARG="
if defined WB set "WBARG=--workbench-root %WB%"

echo [E012] Running %PRESET% dynamic eigenmode campaign...
"%PY%" run_all.py %WBARG% --preset %PRESET% %FORCEPY%
if errorlevel 1 exit /b 30

echo [E012] Packaging outputs...
"%PY%" tools\package_outputs.py
if errorlevel 1 exit /b 31

echo.
echo [E012] PASS - computational campaign completed.
echo [E012] Read outputs\GATES.json and outputs\A052_HANDOFF_STATUS.json
exit /b 0
