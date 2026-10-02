@echo off
setlocal
cd /d "%~dp0"
echo [paper-upgrade] gate selftest
call "%~dp0run_paper_upgrade.cmd" || exit /b 1

rem --- paper-upgrade resume/heartbeat (PU01b) ---
set "PU_FAMILY=A037"
set "PU_TIER=basic"
set "PU_OUT=outputs\basic"
echo.%*| findstr /I /C:"/resume" >nul && set "SST_RESUME=1"
echo.%*| findstr /I /C:"/fresh" >nul && set "SST_FRESH=1"
for /f "delims=" %%W in ('python -c "from pathlib import Path;import sys;p=Path.cwd().resolve();cs=[p,*p.parents];ok=[c for c in cs if (c/'07_scripts'/'paper_upgrade_runtime.py').is_file()];print(ok[0] if ok else '');sys.exit(0 if ok else 2)"') do set "PU_WB=%%W"
if not defined PU_WB (echo [paper-upgrade] ERROR: workbench root not found & exit /b 2)
set "PU_RESUME_FLAG="
if /I "%SST_RESUME%"=="1" set "PU_RESUME_FLAG=--resume"
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" init --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" %PU_RESUME_FLAG% || exit /b 1
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set STAMP=%%i
set OUT=outputs\basic
echo ============================================================
echo SST Chirality-Helicity Transport Polarity Falsifier v0.3.2
echo BASIC BLIND TRAJECTORY-VARIATIONAL CHAIN
echo Dataset: ..\..\..\..\KnotPlot\knots\final
echo Output : %OUT%
echo ============================================================
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "00_setup" %PU_RESUME_FLAG% -- run_00_setup.cmd || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "01_build_native" %PU_RESUME_FLAG% -- run_01_build_native.cmd || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "05_selftest" %PU_RESUME_FLAG% -- run_05_selftest.cmd || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "pc02_qualification" %PU_RESUME_FLAG% -- python pc02_qualification.py || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "campaign" %PU_RESUME_FLAG% -- run_campaign.cmd configs\basic.json "%OUT%" || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "paper_upgrade_nq" %PU_RESUME_FLAG% -- python "%PU_WB%\07_scripts\paper_upgrade_numerics.py" qualify-a037 --out "%PU_OUT%" --write || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "paper_upgrade_cert" %PU_RESUME_FLAG% -- python "%PU_WB%\07_scripts\paper_upgrade_certs.py" emit-a037-campaign --out "%PU_OUT%" --gate "paper_upgrade\gate.py" || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "symmetry_blocks" %PU_RESUME_FLAG% -- python "%PU_WB%\07_scripts\paper_upgrade_certs.py" emit-a037-blocks --out "%PU_OUT%" --gate "paper_upgrade\gate.py" || exit /b 1
echo.
echo ============================================================
echo BLIND RESULT READY
echo SST Chirality-Helicity Transport Polarity Falsifier v0.3.2
echo %OUT%\REPORT_BLIND.md
echo archives\basic_%STAMP%_BLIND.zip
echo ============================================================
echo Then reveal with:
echo   run_40_reveal.cmd "%OUT%"
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" finish --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --status DONE
exit /b 0
