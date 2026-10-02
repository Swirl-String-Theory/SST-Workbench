@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "VENV=%~dp0..\..\.venv"
set "PY=%VENV%\Scripts\python.exe"

echo ============================================================
echo 3_MAXWELL v0.2.0 - install / native build
echo ============================================================
if not exist "%PY%" (
  echo [3_MAXWELL] Creating shared venv: "%VENV%"
  where py >nul 2>&1 || (echo ERROR: Python launcher 'py' not found.& exit /b 2)
  py -m venv "%VENV%" || exit /b 2
)
"%PY%" -m pip install --upgrade pip setuptools wheel || exit /b 2
"%PY%" -m pip install -r requirements.txt || exit /b 2
"%PY%" -m pip install -e . --no-build-isolation || exit /b 2

echo.
echo [3_MAXWELL] Building C++/pybind11 backend with OpenMP...
"%PY%" -m sst_maxwell3_blind.build_ext_if_needed --force --strict
if errorlevel 1 (
  echo.
  echo ERROR: native build failed.
  echo Install Visual Studio 2022 Build Tools with "Desktop development with C++"
  echo and rerun this script. Basic can still be forced through Python,
  echo but the extended campaign intentionally requires native C++.
  exit /b 3
)
"%PY%" -m sst_maxwell3_blind.cli selftest --native
if errorlevel 1 exit /b 4
echo.
echo [3_MAXWELL] INSTALL + NATIVE SELFTEST PASS
exit /b 0
