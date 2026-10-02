@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PRESET=%~1"
if not defined PRESET set "PRESET=max"
set "NEWFLAG="
if /I "%~2"=="new" set "NEWFLAG=--new-run"

if /I not "%PRESET%"=="quick" if /I not "%PRESET%"=="full" if /I not "%PRESET%"=="max" if /I not "%PRESET%"=="extreme" (
  echo ERROR: preset must be quick, full, max, or extreme.
  exit /b 2
)

if not exist "data\ideal_favorites.txt" (
  echo ERROR: bundled database data\ideal_favorites.txt is missing.
  exit /b 3
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/4] Creating Python virtual environment...
  py -3 -m venv .venv
  if errorlevel 1 exit /b 10
)

set "PY=.venv\Scripts\python.exe"

echo [2/4] Installing package and test dependencies...
"%PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 11
"%PY%" -m pip install -e ".[test]" --no-build-isolation
if errorlevel 1 exit /b 12

echo [3/4] Running unit and smoke tests...
if not exist "outputs" mkdir outputs
"%PY%" -m pytest > "outputs\RUN_ALL_pytest.log" 2>&1
if errorlevel 1 (
  type "outputs\RUN_ALL_pytest.log"
  echo ERROR: tests failed; research campaign was not started.
  exit /b 13
)

echo [4/4] Starting %PRESET% research matrix...
echo Scientific gate failures are valid results. Only software/infrastructure failures make this script fail.
"%PY%" "scripts\run_all_research.py" --database "data\ideal_favorites.txt" --preset "%PRESET%" --out-root "outputs\run_all" --resume %NEWFLAG%
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" (
  echo RUN_ALL completed without infrastructure failures.
  echo Read outputs\run_all\LATEST_RUN.txt for the result folder.
) else (
  echo RUN_ALL encountered one or more infrastructure failures. Exit code %RC%.
  echo Scientific FAIL verdicts alone do not produce this error code.
)
exit /b %RC%
