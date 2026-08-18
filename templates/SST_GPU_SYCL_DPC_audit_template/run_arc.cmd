@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo === [A] Intel oneAPI / Level Zero ===
if exist "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" (
  call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat"
  echo [OK] oneAPI setvars loaded.
) else (
  echo [FAIL] oneAPI setvars.bat not found. Install Intel oneAPI toolkit for icpx -fsycl.
  exit /b 1
)

set ONEAPI_DEVICE_SELECTOR=level_zero:0
set SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS=1
set ZES_ENABLE_SYSMAN=1

if not exist build mkdir build

echo === [B] SYCL device probe ===
where icpx >nul 2>&1
if errorlevel 1 (
  echo [FAIL] icpx not on PATH after setvars.
  exit /b 1
)
icpx -fsycl -O2 cpp\list_sycl_devices.cpp -o build\list_sycl_devices.exe
if errorlevel 1 (
  echo [FAIL] list_sycl_devices compile failed.
  exit /b 1
)
build\list_sycl_devices.exe
if errorlevel 1 (
  echo [FAIL] list_sycl_devices exited nonzero.
  exit /b 1
)

echo === [C] GPU-first audit battery ===
python run_all_checks.py --force-build --backend sycl %*
exit /b %errorlevel%
