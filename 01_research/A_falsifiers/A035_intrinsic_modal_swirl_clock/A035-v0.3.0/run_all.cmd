@echo off
setlocal


cd /d "%~dp0"
echo [paper-upgrade] gate selftest
call "%~dp0run_paper_upgrade.cmd" || exit /b 1

rem --- paper-upgrade resume/heartbeat (PU01b) ---
set "PU_FAMILY=A035"
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
echo SST Intrinsic Modal Swirl-Clock Blind Falsifier v0.2.2.7
echo Library-selectable seed-provenance + mesh-certified chain
echo.
echo Usage:
echo   run_all.cmd --libraries=Fremlin,Gilbert,Katlas
echo   run_all.cmd --libraries=Fremlin,Gilbert,Katlas --min-carriers=2
echo   run_all.cmd --libraries=Gilbert,Katlas --min-carriers=2 --kind=links
echo   run_all.cmd --libraries=KnotPlot,Fremlin,Gilbert,Katlas
echo.
echo Fremlin: ..\..\Ideal_Fremlin_Fseries\fremlin
echo Gilbert: ..\..\Ideal_Sources
 echo Katlas:  ..\..\Katlas_Sources_v0.2.2_Outputs  (knots + links)
echo KnotPlot: ..\..\KnotPlot\knots\final  (only when selected)
echo Stage A: T=24 matched topology comparison
echo ============================================================
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "setup" %PU_RESUME_FLAG% -- run_setup.cmd || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "build_native" %PU_RESUME_FLAG% -- run_build_native.cmd || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "selftest" %PU_RESUME_FLAG% -- run_selftest.cmd || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "provenance_scan" %PU_RESUME_FLAG% -- run_provenance_scan.cmd %* || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "basic" %PU_RESUME_FLAG% -- run_basic.cmd %* || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" finish --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --status DONE
