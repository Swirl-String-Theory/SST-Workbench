@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
if exist "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" (
  call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat"
) else (
  echo [FAIL] Intel oneAPI setvars.bat not found.
  exit /b 1
)
set ONEAPI_DEVICE_SELECTOR=level_zero:0
set SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS=1
set ZES_ENABLE_SYSMAN=1
".venv\Scripts\python.exe" -m native_ext.build_ext_if_needed --force --strict || exit /b 1
call run_extended.cmd --backend sycl %*
exit /b %errorlevel%
