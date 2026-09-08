@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo [paper-upgrade] gate selftest
call "%~dp0run_paper_upgrade.cmd" || exit /b 1

rem --- paper-upgrade resume/heartbeat (PU01b) ---

set "PU_FAMILY=D006"

set "PU_TIER=basic"

set "PU_OUT=outputs\basic"

echo.%*| findstr /I /C:"/resume" >nul && set "SST_RESUME=1"

echo.%*| findstr /I /C:"/fresh" >nul && set "SST_FRESH=1"

for /f "delims=" %%W in ('python -c "from pathlib import Path;import sys;p=Path.cwd().resolve();cs=[p,*p.parents];ok=[c for c in cs if (c/'07_scripts'/'paper_upgrade_runtime.py').is_file()];print(ok[0] if ok else '');sys.exit(0 if ok else 2)"') do set "PU_WB=%%W"

if not defined PU_WB (echo [paper-upgrade] ERROR: workbench root not found & exit /b 2)

set "PU_RESUME_FLAG="

if /I "%SST_RESUME%"=="1" set "PU_RESUME_FLAG=--resume"

python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" init --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" %PU_RESUME_FLAG% || exit /b 1

echo ============================================================
echo D006 Minimal Falsification Harness v0.4.0
echo Cheap path: paper-upgrade selftest + synthetic demo + audit
echo ============================================================
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "demo" %PU_RESUME_FLAG% -- python sst_minimal_falsification.py demo --calibration-out synthetic_calibration.json --geometry-out synthetic_geometry.json || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "audit" %PU_RESUME_FLAG% -- python sst_minimal_falsification.py audit --calibration synthetic_calibration.json --geometry synthetic_geometry.json --out synthetic_report.json --abs-tol 1e-3 || exit /b 1
echo DONE: synthetic_report.json
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" finish --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --status DONE

exit /b 0
