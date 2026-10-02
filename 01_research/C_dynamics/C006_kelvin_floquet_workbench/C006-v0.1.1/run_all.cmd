@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set PRESET=quick
if /I "%~1"=="full" set PRESET=full
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TS=%%i
if not defined TS set TS=run
set OUT=audit_out_%PRESET%_%TS%

echo ============================================================
echo SST Kelvin/Floquet Workbench v0.1.1 - FOUR PHASE RUN
echo Preset: %PRESET%
echo Output: %OUT%
echo ============================================================

echo [1/5] Environment / dependency audit
if not exist ".venv\Scripts\python.exe" call "cmd\00_SETUP_VENV.cmd"
if errorlevel 1 goto :fail
.venv\Scripts\python.exe run_dependency_preflight.py >nul 2>&1
if errorlevel 1 call "cmd\00_SETUP_VENV.cmd"
if errorlevel 1 goto :fail

echo [2/5] Native C++ build
call "cmd\01_BUILD_CPP.cmd"
if errorlevel 1 goto :fail

echo [3/5] Native preflight
.venv\Scripts\python.exe run_native_preflight.py
if errorlevel 1 goto :fail

echo [4/5] Tests
call "cmd\02_TEST.cmd"
if errorlevel 1 goto :fail

echo [5/5] Four scientific phases
.venv\Scripts\python.exe run_all.py --preset %PRESET% --out-dir "%OUT%"
set RC=%errorlevel%
if not "%RC%"=="0" goto :failcode

echo ============================================================
echo COMPLETE: %OUT%\audit_summary.json
echo ============================================================
exit /b 0

:fail
echo [SST-KELVIN] FAILED.
exit /b 1
:failcode
echo [SST-KELVIN] Scientific run returned exit code %RC%.
echo Inspect %OUT%\audit_summary.json
exit /b %RC%
