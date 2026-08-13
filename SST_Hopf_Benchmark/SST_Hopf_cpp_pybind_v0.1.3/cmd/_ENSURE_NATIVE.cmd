@echo off
setlocal
cd /d "%~dp0\.."

if not exist ".venv\Scripts\python.exe" (
  call "cmd\00_SETUP_VENV.cmd"
  if errorlevel 1 exit /b 1
)

.venv\Scripts\python.exe -c "import numpy, pybind11, setuptools, wheel" >nul 2>&1
if errorlevel 1 (
  echo [SST-HOPF] Python dependencies incomplete; repairing venv...
  call "cmd\00_SETUP_VENV.cmd"
  if errorlevel 1 exit /b 1
)

set SST_HOPF_FORCE_PYTHON=0
.venv\Scripts\python.exe -c "from sst_hopf_native import load_native; import sys; m=load_native(force_build=False, verbose=False); sys.exit(0 if m is not None else 1)" >nul 2>&1
if errorlevel 1 (
  call "cmd\01_BUILD_CPP.cmd"
  if errorlevel 1 exit /b 1
)
exit /b 0
