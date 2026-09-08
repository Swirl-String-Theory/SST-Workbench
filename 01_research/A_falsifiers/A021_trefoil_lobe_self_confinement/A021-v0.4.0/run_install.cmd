@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PY=python"
where py >nul 2>&1 && set "PY=py -3"
if not exist ".venv\Scripts\python.exe" (
  echo [1/4] Creating .venv...
  %PY% -m venv .venv || exit /b 1
)
echo [2/4] Updating pip/setuptools/wheel...
".venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel || exit /b 1
echo [3/4] Installing requirements...
".venv\Scripts\python.exe" -m pip install -r requirements.txt || exit /b 1
echo [4/4] Building C++/OpenMP extension...
set "SST_DISABLE_SYCL=1"
".venv\Scripts\python.exe" -m native_ext.build_ext_if_needed --force
set "BUILD_RC=%errorlevel%"
set "SST_DISABLE_SYCL="
if not "%BUILD_RC%"=="0" echo [WARN] Native build unavailable; Python fallback remains usable for small tests.
echo [OK] Installation complete.
exit /b 0
