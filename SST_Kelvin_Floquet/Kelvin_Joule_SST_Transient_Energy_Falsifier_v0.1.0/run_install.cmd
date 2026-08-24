@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo Kelvin-Joule SST Transient Energy Falsifier v0.1.0 - INSTALL
echo ============================================================
if not exist .venv\Scripts\python.exe (
  where py >nul 2>&1
  if not errorlevel 1 (
    py -3 -m venv .venv
  ) else (
    python -m venv .venv
  )
  if errorlevel 1 exit /b 1
)
.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
echo [KJ-SST] Building native backend if a compiler is available...
.venv\Scripts\python.exe -m native_ext.build_ext_if_needed --force
if errorlevel 1 (
  echo [WARN] Native build unavailable. Python smoke path remains usable; heavy campaigns require SYCL/OpenMP.
)
echo [OK] Install complete.
exit /b 0
