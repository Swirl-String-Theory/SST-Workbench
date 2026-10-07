@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
set "PY=%CD%\.venv\Scripts\python.exe"
if not exist "%PY%" py -3 -m venv .venv
if errorlevel 1 exit /b %errorlevel%

"%PY%" -m pip install --upgrade pip setuptools wheel pybind11 numpy pytest
if errorlevel 1 exit /b %errorlevel%

rem Remove stale ABI-specific extensions before rebuilding for THIS venv interpreter.
del /q "src\a054_ntaf\_native*.pyd" >nul 2>nul
del /q "src\a054_ntaf\_native*.so" >nul 2>nul

set A054_BUILD_NATIVE=1
"%PY%" -m pip install --no-build-isolation --force-reinstall -e .[test]
if errorlevel 1 (
  echo [WARN] Native build failed. Installing NumPy reference backend for BASIC only.
  set A054_BUILD_NATIVE=0
  "%PY%" -m pip install --no-build-isolation --force-reinstall -e .[test]
  if errorlevel 1 exit /b %errorlevel%
)

"%PY%" -c "import sys,a054_ntaf; from a054_ntaf.physics import qualify_backend; print('PYTHON',sys.executable); print('VERSION',sys.version); print('A054',a054_ntaf.__version__); print('BACKEND',qualify_backend('prefer_native'))"
exit /b %errorlevel%
