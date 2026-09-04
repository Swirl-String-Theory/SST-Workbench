@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo === [A] Session oneAPI for Arc A770 (no permanent Windows PATH) ===

set "ONEAPI_SETVARS="
if exist "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" set "ONEAPI_SETVARS=C:\Program Files (x86)\Intel\oneAPI\setvars.bat"
if not defined ONEAPI_SETVARS if exist "C:\Program Files\Intel\oneAPI\setvars.bat" set "ONEAPI_SETVARS=C:\Program Files\Intel\oneAPI\setvars.bat"
if not defined ONEAPI_SETVARS (
  echo [FAIL] Intel oneAPI setvars.bat not found. Install oneAPI DPC++ for Arc A770.
  exit /b 1
)
call "%ONEAPI_SETVARS%" >nul || exit /b 1
echo [OK] oneAPI setvars loaded for this session only.

set "ONEAPI_DEVICE_SELECTOR=level_zero:gpu"
set "SYCL_CACHE_PERSISTENT=0"
set "SST_SYCL_ALLOW_FP32=1"

if exist ".venv\Scripts\python.exe" (
  set "PY=.venv\Scripts\python.exe"
) else (
  set "PY=python"
)

if not exist build mkdir build

echo === [B] External SYCL worker smoke ===
"%PY%" tools\build_sycl_worker.py --force --strict
if errorlevel 1 (
  echo [FAIL] sst_sycl_worker build/probe failed.
  exit /b 1
)
"%PY%" -X faulthandler tools\sycl_worker_smoke.py
if errorlevel 1 (
  echo [FAIL] sycl_worker_smoke failed.
  exit /b 1
)

echo === [C] Host OpenMP .pyd + GPU worker audit battery ===
for %%I in ("%~dp0.") do set "FOLDER=%%~nxI"
set "OUTDIR=%~dp0%FOLDER%_outputs"
echo %*| findstr /I /C:"--out-dir" >nul
if errorlevel 1 (
  "%PY%" run_all_checks.py --force-build --backend sycl --out-dir "%OUTDIR%" %*
) else (
  "%PY%" run_all_checks.py --force-build --backend sycl %*
)
exit /b %errorlevel%
