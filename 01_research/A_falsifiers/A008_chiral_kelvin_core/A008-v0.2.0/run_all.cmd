@echo off
setlocal

cd /d "%~dp0"
echo [paper-upgrade] gate selftest
call "%~dp0run_paper_upgrade.cmd" || exit /b 1

rem --- paper-upgrade resume/heartbeat (PU01b) ---
set "PU_FAMILY=A008"
set "PU_TIER=quick"
set "PU_OUT=outputs\quick"
echo.%*| findstr /I /C:"/resume" >nul && set "SST_RESUME=1"
echo.%*| findstr /I /C:"/fresh" >nul && set "SST_FRESH=1"
for /f "delims=" %%W in ('python -c "from pathlib import Path;import sys;p=Path.cwd().resolve();cs=[p,*p.parents];ok=[c for c in cs if (c/'07_scripts'/'paper_upgrade_runtime.py').is_file()];print(ok[0] if ok else '');sys.exit(0 if ok else 2)"') do set "PU_WB=%%W"
if not defined PU_WB (echo [paper-upgrade] ERROR: workbench root not found & exit /b 2)
set "PU_RESUME_FLAG="
if /I "%SST_RESUME%"=="1" set "PU_RESUME_FLAG=--resume"
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" init --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" %PU_RESUME_FLAG% || exit /b 1
set PRESET=%1

if "%PRESET%"=="" (
    set PRESET=quick
)

echo.
echo ==============================================
echo SST Chiral Kelvin Falsification v0.1.3.1
echo Preset: %PRESET%
echo ==============================================
echo.

echo [1/2] Building/checking native pybind extension...
python -m chiral_kelvin.build_ext_if_needed --strict

if errorlevel 1 (
    echo.
    echo ERROR: native build failed.
    exit /b 1
)

echo.
echo [2/2] Running audit and convergence ladder...

python run_all_checks.py ^
    --preset %PRESET% ^
    --out-dir audit_out_v0131

set RC=%errorlevel%

echo.
echo ==============================================
echo Finished with exit code %RC%
echo Results: audit_out_v0131
echo ==============================================
echo.

python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" finish --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --status DONE
exit /b %RC%
