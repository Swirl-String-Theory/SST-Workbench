@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo [paper-upgrade] gate selftest
call "%~dp0run_paper_upgrade.cmd" || exit /b 1

rem --- paper-upgrade resume/heartbeat (PU01b) ---
set "PU_FAMILY=A023"
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
echo SST Multi-Topology Knot/Link TBK + RPO/Floquet v0.4.8
echo ============================================================
echo [SST] run_all uses confirmatory CPU/OpenMP FP64 only.
echo [SST] For Arc/SYCL use run_sycl_worker_smoke.cmd or *_sycl.cmd explicitly.
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "install" %PU_RESUME_FLAG% -- run_install.cmd || exit /b 1
if errorlevel 1 exit /b %errorlevel%
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "panel_basic" %PU_RESUME_FLAG% -- run_panel_basic.cmd || exit /b 1
set BASIC_RC=%errorlevel%
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "panel_extended" %PU_RESUME_FLAG% -- run_panel_extended.cmd || exit /b 1
set EXT_RC=%errorlevel%
echo ============================================================
echo Completed. BASIC rc=%BASIC_RC% EXTENDED rc=%EXT_RC%
echo PASS/FAIL are scientific classifications; script errors are separate.
echo ============================================================
if not "%EXT_RC%"=="0" exit /b %EXT_RC%
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" finish --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --status DONE
exit /b %BASIC_RC%
