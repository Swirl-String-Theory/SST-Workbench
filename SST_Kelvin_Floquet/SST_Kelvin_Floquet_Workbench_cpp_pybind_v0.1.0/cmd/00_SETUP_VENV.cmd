@echo off
setlocal
cd /d "%~dp0\.."
if not exist ".venv\Scripts\python.exe" (
  echo [SST-KELVIN] Creating .venv ...
  python -m venv .venv
  if errorlevel 1 (
    py -3 -m venv .venv
    if errorlevel 1 exit /b 1
  )
)
call ".venv\Scripts\activate.bat"
echo [SST-KELVIN] Upgrading build tooling ...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1
echo [SST-KELVIN] Installing requirements ...
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
python run_dependency_preflight.py
if errorlevel 1 exit /b 1
echo [SST-KELVIN] Environment ready.
exit /b 0
