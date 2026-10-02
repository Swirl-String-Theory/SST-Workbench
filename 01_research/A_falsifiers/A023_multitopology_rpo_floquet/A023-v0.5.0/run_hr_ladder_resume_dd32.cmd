@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if "%~1"=="" echo Usage: run_hr_ladder_resume_dd32.cmd ^<existing_output_dir^> [start_rung] & exit /b 2
set "OUT=%~1"
set "START=%~2"
if "%START%"=="" set "START=0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
set "ONEAPI_SETVARS="
if exist "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" set "ONEAPI_SETVARS=C:\Program Files (x86)\Intel\oneAPI\setvars.bat"
if not defined ONEAPI_SETVARS if exist "C:\Program Files\Intel\oneAPI\setvars.bat" set "ONEAPI_SETVARS=C:\Program Files\Intel\oneAPI\setvars.bat"
if not defined ONEAPI_SETVARS echo [FAIL] Intel oneAPI setvars.bat not found. & exit /b 1
call "%ONEAPI_SETVARS%" >nul || exit /b 1
set "ONEAPI_DEVICE_SELECTOR=level_zero:gpu"
set "SYCL_CACHE_PERSISTENT=0"
set "SST_SYCL_ALLOW_FP32=1"
".venv\Scripts\python.exe" tools\build_sycl_worker.py --strict || exit /b 1
".venv\Scripts\python.exe" tools\sycl_dd32_smoke.py --strict || exit /b 1
".venv\Scripts\python.exe" run_hr_ladder.py --out-dir "%OUT%" --backend sycl-dd32 --start-rung %START%
exit /b %errorlevel%
