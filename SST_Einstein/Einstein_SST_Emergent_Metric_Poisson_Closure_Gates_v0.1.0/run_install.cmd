@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo [SST] Installing Einstein-SST Closure Gates v0.1.0
echo ============================================================
if not exist ".venv\Scripts\python.exe" (
  echo [SST] Creating local virtual environment...
  if defined SST_PYTHON ("%SST_PYTHON%" -m venv .venv) else (py -3 -m venv .venv)
  if errorlevel 1 exit /b 1
)
set "VPY=.venv\Scripts\python.exe"
"%VPY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
"%VPY%" -m pip install -e . --no-build-isolation
if errorlevel 1 (
 echo [SST] Install/build failed. Prefer Visual Studio 2022 Build Tools with Desktop C++.
 echo [SST] For a no-OpenMP diagnostic build: set SST_DISABLE_OPENMP=1 and rerun.
 exit /b 1
)
echo [SST] Install complete.
