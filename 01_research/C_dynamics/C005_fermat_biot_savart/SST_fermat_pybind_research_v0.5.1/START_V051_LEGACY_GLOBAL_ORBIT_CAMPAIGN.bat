@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if defined VIRTUAL_ENV (
    set "PYTHON_EXE=python"
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    echo ERROR: no active virtual environment and .venv\Scripts\python.exe was not found.
    pause
    exit /b 1
)

"%PYTHON_EXE%" run_global_orbit_campaign.py ^
  --preset full ^
  --require-native ^
  --resume ^
  --out-root v0.5.1_global_orbit_output ^
  --archive SST_fermat_pybind_research_v0.5.1_global_orbit_results.zip %*
set "RUN_RC=%ERRORLEVEL%"
echo.
if "%RUN_RC%"=="0" (
    echo GLOBAL ORBIT CAMPAIGN COMPUTATION COMPLETED.
    echo Inspect campaign_summary.json for the scientific certification flags.
) else (
    echo CAMPAIGN STOPPED OR FAILED. Inspect v0.5.1_global_orbit_output\logs.
    echo Run this BAT again to resume completed steps.
)
pause
exit /b %RUN_RC%
