@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if exist "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" (
  call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat"
) else (
  echo [FAIL] Intel oneAPI setvars.bat not found.
  exit /b 1
)
set ONEAPI_DEVICE_SELECTOR=level_zero:0
set SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS=1
set ZES_ENABLE_SYSMAN=1
where icpx >nul 2>&1
if errorlevel 1 (echo [FAIL] icpx not found after setvars.& exit /b 1)
if not exist build mkdir build
icpx -fsycl -O2 cpp\list_sycl_devices.cpp -o build\list_sycl_devices.exe
if errorlevel 1 exit /b 1
build\list_sycl_devices.exe
if errorlevel 1 exit /b 1
if not exist .venv\Scripts\python.exe call run_install.cmd
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe run_all_checks.py --force-build --backend sycl
exit /b %errorlevel%
