@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
set "ONEAPI_SETVARS="
if exist "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" set "ONEAPI_SETVARS=C:\Program Files (x86)\Intel\oneAPI\setvars.bat"
if not defined ONEAPI_SETVARS if exist "C:\Program Files\Intel\oneAPI\setvars.bat" set "ONEAPI_SETVARS=C:\Program Files\Intel\oneAPI\setvars.bat"
if not defined ONEAPI_SETVARS echo [FAIL] Intel oneAPI setvars.bat not found. & exit /b 1
call "%ONEAPI_SETVARS%" >nul || exit /b 1
set "SST_DISABLE_SYCL=0"
set "ONEAPI_DEVICE_SELECTOR=level_zero:0"
".venv\Scripts\python.exe" -m native_ext.build_ext_if_needed --force --strict --require-sycl || exit /b 1
set "TSFILE=.sst_timestamp_archive_extra_sycl.tmp"
".venv\Scripts\python.exe" tools\timestamp.py > "%TSFILE%" || exit /b 1
set /p TS=<"%TSFILE%"
del /q "%TSFILE%" >nul 2>&1
".venv\Scripts\python.exe" run_archive_campaign.py --config configs\archive_extra_extended.json --out-dir "outputs_archive_extra_extended_sycl_%TS%" --backend sycl
exit /b %errorlevel%
