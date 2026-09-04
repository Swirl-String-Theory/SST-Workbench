@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo SST Fermat pybind research v0.5.0 - FULL CAMPAIGN
echo Sequential native audit, atlases, convergence, scale, symmetry
echo Final archive: SST_fermat_pybind_research_v0.5.0_results.zip
echo ============================================================
echo.

if defined VIRTUAL_ENV (
    set "PYTHON_EXE=python"
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" run_full_campaign.py ^
  --preset full ^
  --require-native ^
  --resume ^
  --out-root v0.5.0_campaign_output ^
  --archive SST_fermat_pybind_research_v0.5.0_results.zip %*

set "RUN_RC=%ERRORLEVEL%"
echo.
if "%RUN_RC%"=="0" (
    echo FULL CAMPAIGN COMPLETED SUCCESSFULLY.
) else (
    echo CAMPAIGN STOPPED OR FAILED. Inspect v0.5.0_campaign_output\logs.
    echo Run this same BAT again to resume completed steps.
)
echo.
pause
exit /b %RUN_RC%
