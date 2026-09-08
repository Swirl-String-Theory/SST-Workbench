@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if exist "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat"
set "SST_ONEAPI_DLL_DIR=%ONEAPI_ROOT%\compiler\latest\bin"
set "SST_DISABLE_SYCL=0"
set "ONEAPI_DEVICE_SELECTOR=level_zero:gpu"
set "SYCL_CACHE_PERSISTENT=0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd
".venv\Scripts\python.exe" -X faulthandler tools\sycl_diagnostics.py
set RC=%ERRORLEVEL%
echo [SST] SYCL diagnostics RC=%RC%
exit /b %RC%
