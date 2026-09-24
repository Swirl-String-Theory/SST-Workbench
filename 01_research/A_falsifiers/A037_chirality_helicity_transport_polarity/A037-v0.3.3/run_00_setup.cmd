@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo SST Chirality-Helicity Falsifier v0.2.0 - environment setup
echo ============================================================
if not exist .venv\Scripts\python.exe (
  where py >nul 2>nul
  if not errorlevel 1 (py -3 -m venv .venv) else (python -m venv .venv)
  if errorlevel 1 exit /b 1
)
.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel || exit /b 1
.venv\Scripts\python.exe -m pip install -r requirements.txt || exit /b 1
exit /b 0
