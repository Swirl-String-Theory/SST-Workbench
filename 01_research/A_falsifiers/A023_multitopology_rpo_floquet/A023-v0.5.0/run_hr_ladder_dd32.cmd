@echo off
setlocal EnableExtensions
cd /d "%~dp0"
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
set "TSFILE=.sst_timestamp_hr_ladder.tmp"
".venv\Scripts\python.exe" tools\timestamp.py > "%TSFILE%" || exit /b 1
set /p TS=<"%TSFILE%"
del /q "%TSFILE%" >nul 2>&1
set "OUT=outputs_hr_ladder_dd32_%TS%"
echo [SST-LADDER] Starting all 127 geometries through six preregistered rungs.
echo [SST-LADDER] Output: %OUT%
".venv\Scripts\python.exe" run_hr_ladder.py --out-dir "%OUT%" --backend sycl-dd32
exit /b %errorlevel%
