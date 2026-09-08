@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo [paper-upgrade] gate selftest
call "%~dp0run_paper_upgrade.cmd" || exit /b 1

rem --- paper-upgrade resume/heartbeat (PU01b) ---
set "PU_FAMILY=C006"
set "PU_TIER=quick"
set "PU_OUT=outputs\quick"
echo.%*| findstr /I /C:"/resume" >nul && set "SST_RESUME=1"
echo.%*| findstr /I /C:"/fresh" >nul && set "SST_FRESH=1"
for /f "delims=" %%W in ('python -c "from pathlib import Path;import sys;p=Path.cwd().resolve();cs=[p,*p.parents];ok=[c for c in cs if (c/'07_scripts'/'paper_upgrade_runtime.py').is_file()];print(ok[0] if ok else '');sys.exit(0 if ok else 2)"') do set "PU_WB=%%W"
if not defined PU_WB (echo [paper-upgrade] ERROR: workbench root not found & exit /b 2)
set "PU_RESUME_FLAG="
if /I "%SST_RESUME%"=="1" set "PU_RESUME_FLAG=--resume"
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" init --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" %PU_RESUME_FLAG% || exit /b 1
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
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" finish --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --status DONE
exit /b 0

:fail
echo [SST-KELVIN] FAILED.
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" finish --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --status FAILED 2>nul
exit /b 1
:failcode
echo [SST-KELVIN] Scientific run returned exit code %RC%.
echo Inspect %OUT%\audit_summary.json
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" finish --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --status FAILED
exit /b %RC%
