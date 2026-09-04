@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
if exist "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" (call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat") else (echo [FAIL] oneAPI not found.& exit /b 1)
set ONEAPI_DEVICE_SELECTOR=level_zero:0
set SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS=1
set ZES_ENABLE_SYSMAN=1
if not exist .venv\Scripts\python.exe call run_install.cmd
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m native_ext.build_ext_if_needed --force
if errorlevel 1 exit /b 1
call run_extended.cmd "%DATASET%" sycl
exit /b %errorlevel%
