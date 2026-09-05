@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo SST Local Thread Texture Falsifier v0.2.1 - environment setup
echo ============================================================
if not exist ".venv\Scripts\python.exe" (
  where py >nul 2>nul
  if not errorlevel 1 (
    py -3.14 -m venv .venv 2>nul
    if errorlevel 1 py -3 -m venv .venv
  ) else (
    python -m venv .venv
  )
)
if not exist ".venv\Scripts\python.exe" (
  echo [FAIL] Could not create .venv
  exit /b 1
)
.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b %errorlevel%
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b %errorlevel%
.venv\Scripts\python.exe run_dependency_preflight.py
exit /b %errorlevel%
