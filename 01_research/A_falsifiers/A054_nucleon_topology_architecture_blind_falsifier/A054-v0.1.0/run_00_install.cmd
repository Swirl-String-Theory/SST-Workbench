@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
if errorlevel 1 exit /b %errorlevel%
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel pybind11 numpy pytest
if errorlevel 1 exit /b %errorlevel%
set A054_BUILD_NATIVE=1
python -m pip install --no-build-isolation -e .[test]
if errorlevel 1 (
  echo [WARN] Native build failed. Installing NumPy reference backend for BASIC only.
  set A054_BUILD_NATIVE=0
  python -m pip install --no-build-isolation -e .[test]
  if errorlevel 1 exit /b %errorlevel%
)
python -c "import a054_ntaf; print('A054',a054_ntaf.__version__)"
exit /b %errorlevel%
