@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "ROOT=%CD%"
for %%I in ("%ROOT%\..\..") do set "WORKBENCH=%%~fI"
set "VENV=%WORKBENCH%\.venv"
set "PY=%VENV%\Scripts\python.exe"
echo ============================================================
echo 5_Maxwell SST Reciprocal Falsifier v0.2.0 - INSTALL
echo ============================================================
echo [5_Maxwell] Workbench: "%WORKBENCH%"
if not exist "%PY%" (
  echo [5_Maxwell] Creating shared venv: "%VENV%"
  where py >nul 2>nul
  if errorlevel 1 (
    echo ERROR: Python launcher 'py' not found. Install Python 3.11+ first.
    exit /b 2
  )
  py -3 -m venv "%VENV%" || exit /b 2
)
"%PY%" -m pip install --upgrade pip setuptools wheel || exit /b 2
"%PY%" -m pip install -r requirements.txt || exit /b 2
"%PY%" -m maxwell5_native.build_ext_if_needed --force --strict || (
  echo ERROR: C++ extension build failed.
  echo Install Visual Studio Build Tools with Desktop development with C++ and retry.
  exit /b 3
)
"%PY%" tests\run_tests.py || exit /b 4
echo.
echo [5_Maxwell] INSTALL PASS - native pybind11 backend built and tested.
exit /b 0
