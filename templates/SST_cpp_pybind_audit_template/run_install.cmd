@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo SST cpp_pybind audit template - INSTALL
echo ============================================================

if not exist ".venv\Scripts\python.exe" (
  echo [1/3] Creating local virtual environment...
  where py >nul 2>&1
  if not errorlevel 1 (
    py -3 -m venv .venv
  ) else (
    python -m venv .venv
  )
  if errorlevel 1 goto :fail
) else (
  echo [1/3] Local virtual environment already exists.
)

set "PY=.venv\Scripts\python.exe"

echo [2/3] Upgrading pip / setuptools / wheel...
"%PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :fail

echo [3/3] Installing requirements...
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo [OK] Python environment ready.
exit /b 0

:fail
echo [FAIL] Install failed.
exit /b 1
