@echo off
setlocal
cd /d "%~dp0\.."
if not exist ".venv\Scripts\python.exe" (
  echo [SST-HOPF] Creating .venv ...
  py -m venv .venv 2>nul || python -m venv .venv
  if errorlevel 1 exit /b 1
)
call ".venv\Scripts\activate.bat"

echo [SST-HOPF] Upgrading Python build tooling ...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1

echo [SST-HOPF] Installing runtime/native requirements ...
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo [SST-HOPF] Dependency preflight ...
python -c "import numpy, pybind11, setuptools, wheel; print('[SST-HOPF] numpy', numpy.__version__); print('[SST-HOPF] pybind11', pybind11.__version__); print('[SST-HOPF] setuptools', setuptools.__version__); print('[SST-HOPF] wheel', wheel.__version__)"
if errorlevel 1 exit /b 1

echo [SST-HOPF] Environment ready.
exit /b 0
