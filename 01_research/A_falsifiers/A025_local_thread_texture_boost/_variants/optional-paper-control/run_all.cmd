@echo off
setlocal
cd /d "%~dp0"
echo [paper-upgrade] gate selftest
call "%~dp0run_paper_upgrade.cmd" || exit /b 1

rem --- paper-upgrade resume/heartbeat (PU01b) ---
set "PU_FAMILY=A025"
set "PU_TIER=basic"
set "PU_OUT=outputs\basic"
echo.%*| findstr /I /C:"/resume" >nul && set "SST_RESUME=1"
echo.%*| findstr /I /C:"/fresh" >nul && set "SST_FRESH=1"
for /f "delims=" %%W in ('python -c "from pathlib import Path;import sys;p=Path.cwd().resolve();cs=[p,*p.parents];ok=[c for c in cs if (c/'07_scripts'/'paper_upgrade_runtime.py').is_file()];print(ok[0] if ok else '');sys.exit(0 if ok else 2)"') do set "PU_WB=%%W"
if not defined PU_WB (echo [paper-upgrade] ERROR: workbench root not found & exit /b 2)
set "PU_RESUME_FLAG="
if /I "%SST_RESUME%"=="1" set "PU_RESUME_FLAG=--resume"
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" init --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" %PU_RESUME_FLAG% || exit /b 1
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
echo ============================================================
echo SST Explicit Closed Vortex-Thread Blind Falsifier v0.3.0
echo BASIC one-click chain
echo Dataset: %DATASET%
echo ============================================================
echo [1/5] Install / update environment
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "install" %PU_RESUME_FLAG% -- run_install.cmd || exit /b 1
if errorlevel 1 goto :fail
echo [2/5] Strict C++17/pybind11 native build
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "build_native" %PU_RESUME_FLAG% -- run_build_native.cmd || exit /b 1
if errorlevel 1 goto :fail
echo [3/5] Native-vs-Python + exact-segment/RK4/boost/closure selftest
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "selftest" %PU_RESUME_FLAG% -- run_selftest.cmd || exit /b 1
if errorlevel 1 goto :fail
echo [4/5] Blind BASIC nonlinear thread campaign
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "basic" %PU_RESUME_FLAG% -- run_basic.cmd "%DATASET%" || exit /b 1
if errorlevel 1 goto :fail
echo [5/5] Complete - inspect newest outputs_basic_*\unblinded_report.json
echo ============================================================
echo PASS - execution and structural chain completed.
echo Bridge PASS/FAIL is scientific output; inspect the report.
echo ============================================================
exit /b 0
:fail
echo ============================================================
echo FAIL - chain stopped with errorlevel %errorlevel%
echo ============================================================
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" finish --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --status DONE
exit /b %errorlevel%
