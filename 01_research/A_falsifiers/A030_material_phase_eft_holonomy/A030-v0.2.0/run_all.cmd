@echo off
setlocal
cd /d "%~dp0"
echo [paper-upgrade] gate selftest
call "%~dp0run_paper_upgrade.cmd" || exit /b 1

rem --- paper-upgrade resume/heartbeat (PU01b) ---
set "PU_FAMILY=A030"
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
echo SST Material-Coordinate / Phase-Shift EFT Falsifier v0.1.1
echo One-click chain
echo Dataset: %DATASET%
echo ============================================================
echo [1/3] Setup
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "setup" %PU_RESUME_FLAG% -- run_setup.cmd || exit /b 1
if errorlevel 1 exit /b 1
echo [2/3] Basic
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "basic" %PU_RESUME_FLAG% -- run_basic.cmd "%DATASET%" "outputs\basic" || exit /b 1
if errorlevel 1 exit /b 1
echo [3/3] Extended
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "extended" %PU_RESUME_FLAG% -- run_extended.cmd "%DATASET%" "outputs\extended" || exit /b 1
if errorlevel 1 exit /b 1
echo ============================================================
echo DONE
echo Basic   : outputs\basic\REPORT.md
echo Extended: outputs\extended\REPORT.md
echo ============================================================
endlocal
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" finish --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --status DONE
