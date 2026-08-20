@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
set "ONEAPI_SETVARS="
if exist "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" set "ONEAPI_SETVARS=C:\Program Files (x86)\Intel\oneAPI\setvars.bat"
if not defined ONEAPI_SETVARS if exist "C:\Program Files\Intel\oneAPI\setvars.bat" set "ONEAPI_SETVARS=C:\Program Files\Intel\oneAPI\setvars.bat"
if not defined ONEAPI_SETVARS (
  echo [FAIL] Intel oneAPI setvars.bat not found.
  exit /b 1
)
echo [SST] Initializing Intel oneAPI environment...
call "%ONEAPI_SETVARS%" >nul
if errorlevel 1 (
  echo [FAIL] oneAPI setvars.bat failed.
  exit /b 1
)
set "SST_DISABLE_SYCL=0"
set "ONEAPI_DEVICE_SELECTOR=level_zero:0"
set "SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS=1"
set "ZES_ENABLE_SYSMAN=1"
".venv\Scripts\python.exe" -m native_ext.build_ext_if_needed --force --strict --require-sycl || exit /b 1
".venv\Scripts\python.exe" -c "from native_ext.core import load_native,native_info; m=load_native(skip_build=True); i=native_info(m); print('[SST] SYCL backend:', i); raise SystemExit(0 if i.get('sycl_compiled') else 3)" || exit /b 1
call run_extended.cmd --backend sycl %*
exit /b %errorlevel%
