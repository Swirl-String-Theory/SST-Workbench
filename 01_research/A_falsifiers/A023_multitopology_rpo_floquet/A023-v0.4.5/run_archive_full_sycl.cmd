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
echo [SST] Building external SYCL worker; Python will NOT import SYCL device kernels.
".venv\Scripts\python.exe" tools\build_sycl_worker.py --force --strict || exit /b 1
echo [SST] Running worker smoke/parity...
".venv\Scripts\python.exe" tools\sycl_worker_smoke.py || exit /b 1
echo [WARN] Arc without native FP64: this FULL SYCL campaign is FP32 SCREENING ONLY.
echo [WARN] CPU/OpenMP FP64 remains confirmatory for gate decisions near thresholds/RPO/Floquet.
set "TSFILE=.sst_timestamp_archive_full_sycl.tmp"
".venv\Scripts\python.exe" tools\timestamp.py > "%TSFILE%" || exit /b 1
set /p TS=<"%TSFILE%"
del /q "%TSFILE%" >nul 2>&1
".venv\Scripts\python.exe" run_archive_campaign.py --config configs\archive_full.json --out-dir "outputs_archive_full_sycl_fp32_screen_%TS%" --backend sycl
exit /b %errorlevel%
