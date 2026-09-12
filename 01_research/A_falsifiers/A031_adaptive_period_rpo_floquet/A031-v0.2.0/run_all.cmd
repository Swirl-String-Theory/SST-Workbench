@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo [paper-upgrade] gate selftest
call "%~dp0run_paper_upgrade.cmd" || exit /b 1

rem --- paper-upgrade resume/heartbeat (PU01b) ---
set "PU_FAMILY=A031"
set "PU_TIER=basic"
set "PU_OUT=outputs\basic"
echo.%*| findstr /I /C:"/resume" >nul && set "SST_RESUME=1"
echo.%*| findstr /I /C:"/fresh" >nul && set "SST_FRESH=1"
for /f "delims=" %%W in ('python -c "from pathlib import Path;import sys;p=Path.cwd().resolve();cs=[p,*p.parents];ok=[c for c in cs if (c/'07_scripts'/'paper_upgrade_runtime.py').is_file()];print(ok[0] if ok else '');sys.exit(0 if ok else 2)"') do set "PU_WB=%%W"
if not defined PU_WB (echo [paper-upgrade] ERROR: workbench root not found & exit /b 2)
set "PU_RESUME_FLAG="
if /I "%SST_RESUME%"=="1" set "PU_RESUME_FLAG=--resume"
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" init --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" %PU_RESUME_FLAG% || exit /b 1
if not defined SST_V048_DIR set "SST_V048_DIR=%PU_WB%\01_research\A_falsifiers\A023_multitopology_rpo_floquet\A023-v0.4.8"
if not defined SST_ATLAS_ROOT set "SST_ATLAS_ROOT=%PU_WB%\01_research\D_benchmarks\D009_knotplot_parameter_atlas\D009-v0.3.0"
if not exist "%SST_V048_DIR%\VERSION.json" (
  echo ERROR: target v0.4.8 not found: %SST_V048_DIR%
  exit /b 2
)
if not exist "%SST_V048_DIR%\.venv\Scripts\python.exe" (
  echo [RPO] target venv missing - running v0.4.8 installer...
  python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "_SST_V048_DIR_" %PU_RESUME_FLAG% -- "%SST_V048_DIR%\run_install.cmd" || exit /b 1
  if errorlevel 1 exit /b %ERRORLEVEL%
)
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "preflight" %PU_RESUME_FLAG% -- run_preflight.cmd || exit /b 1
if errorlevel 1 exit /b %ERRORLEVEL%
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "extended" %PU_RESUME_FLAG% -- run_extended.cmd || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" finish --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --status DONE
exit /b %ERRORLEVEL%
