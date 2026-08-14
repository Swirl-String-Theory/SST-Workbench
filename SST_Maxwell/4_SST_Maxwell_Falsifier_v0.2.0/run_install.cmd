@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo [4_SST] Installing workbench v0.2.0...
if not exist ".venv\Scripts\python.exe" (
  where py >nul 2>nul
  if not errorlevel 1 (
    py -3 -m venv .venv
  ) else (
    python -m venv .venv
  )
  if errorlevel 1 exit /b %errorlevel%
)
set "PY=%CD%\.venv\Scripts\python.exe"
"%PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b %errorlevel%
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 exit /b %errorlevel%
"%PY%" -m pip install -e .
if errorlevel 1 exit /b %errorlevel%
echo [4_SST] Attempting optimized C++/pybind11 build...
"%PY%" -m native_ext.build_ext_if_needed --force
"%PY%" -m maxwell_sst.cli native-info
echo [4_SST] Install complete.
exit /b 0
