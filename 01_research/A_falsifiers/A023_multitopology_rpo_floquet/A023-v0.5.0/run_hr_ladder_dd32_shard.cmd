@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if "%~3"=="" echo Usage: run_hr_ladder_dd32_shard.cmd ^<shard_count^> ^<shard_index^> ^<output_dir^> & exit /b 2
set "COUNT=%~1"
set "INDEX=%~2"
set "OUT=%~3"
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
set "SST_DISABLE_SYCL=1"
".venv\Scripts\python.exe" -m native_ext.build_ext_if_needed --strict || exit /b 1
set "SST_DISABLE_SYCL="
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
".venv\Scripts\python.exe" run_hr_ladder.py --out-dir "%OUT%" --backend sycl-dd32 --shard-count %COUNT% --shard-index %INDEX%
exit /b %errorlevel%
