@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo [paper-upgrade] gate selftest
call "%~dp0run_paper_upgrade.cmd" || exit /b 1

rem --- paper-upgrade resume/heartbeat (PU01b) ---
set "PU_FAMILY=A021"
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
echo SST Trefoil Coupled TBK + RPO/Floquet Falsifier v0.3.0
echo ============================================================
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "install" %PU_RESUME_FLAG% -- run_install.cmd || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "test" %PU_RESUME_FLAG% -- run_test.cmd || exit /b 1
if not defined SST_A034_CERT set "SST_A034_CERT=%PU_WB%\01_research\A_falsifiers\A034_qhp_stability_landscape\A034-v0.2.1\outputs\basic\paper_upgrade\certificate.json"
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "consume_a034" %PU_RESUME_FLAG% -- python "%PU_WB%\07_scripts\paper_upgrade_certs.py" consume-a034 --cert "%SST_A034_CERT%" --gate "paper_upgrade\gate.py" || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "basic" %PU_RESUME_FLAG% -- run_basic.cmd || exit /b 1
set BASIC_RC=%errorlevel%
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "extended" %PU_RESUME_FLAG% -- run_extended.cmd || exit /b 1
set EXT_RC=%errorlevel%
echo ============================================================
echo Completed. BASIC rc=%BASIC_RC% EXTENDED rc=%EXT_RC%
echo Scientific FAIL is a valid completed result; INCONCLUSIVE returns rc=2.
echo ============================================================
if %BASIC_RC%==2 exit /b 2
if %EXT_RC%==2 exit /b 2
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" finish --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --status DONE
exit /b 0
