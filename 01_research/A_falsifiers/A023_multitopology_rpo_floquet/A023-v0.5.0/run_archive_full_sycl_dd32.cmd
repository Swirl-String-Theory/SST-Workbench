@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
set "SST_DISABLE_SYCL=1"
".venv\Scripts\python.exe" -m native_ext.build_ext_if_needed --force --strict || exit /b 1
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
echo [WARN] FULL DD32 is an experimental high-precision GPU candidate, not native/IEEE FP64.
echo [WARN] Near-threshold gates, RPO and Floquet still require CPU/OpenMP FP64 confirmation until parity is demonstrated.
set "TSFILE=.sst_timestamp_archive_full_dd32.tmp"
".venv\Scripts\python.exe" tools\timestamp.py > "%TSFILE%" || exit /b 1
set /p TS=<"%TSFILE%"
del /q "%TSFILE%" >nul 2>&1
".venv\Scripts\python.exe" run_archive_campaign.py --config configs\archive_full.json --out-dir "outputs_archive_full_sycl_dd32_%TS%" --backend sycl-dd32
exit /b %errorlevel%
