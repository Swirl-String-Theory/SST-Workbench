@echo off
setlocal EnableExtensions
cd /d "%~dp0"
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
set "TSFILE=.sst_timestamp_spectral_ext.tmp"
".venv\Scripts\python.exe" tools\timestamp.py > "%TSFILE%" || exit /b 1
set /p TS=<"%TSFILE%"
del /q "%TSFILE%" >nul 2>&1
set "OUT=outputs_spectral_extension_dd32_%TS%"
set "BASELINE=%~1"
if not "%~2"=="" set "OUT=%~2"
echo [SST-SPECTRAL] v0.4.8 adaptive k_max 16-24-32-48-64, N=720.
echo [SST-SPECTRAL] Output: %OUT%
if defined BASELINE (
  echo [SST-SPECTRAL] Reusing v0.4.7 baseline: %BASELINE%
  ".venv\Scripts\python.exe" run_spectral_extension.py --out-dir "%OUT%" --backend sycl-dd32 --baseline "%BASELINE%"
) else (
  echo [SST-SPECTRAL] No baseline argument supplied. The runner will auto-find a sibling v0.4.7 output or recompute k16.
  ".venv\Scripts\python.exe" run_spectral_extension.py --out-dir "%OUT%" --backend sycl-dd32
)
exit /b %errorlevel%
