@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if defined VIRTUAL_ENV (
    set "PYTHON_EXE=python"
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)
"%PYTHON_EXE%" run_full_campaign.py --preset smoke --require-native --overwrite --out-root v0.6.1_smoke_output --archive SST_fermat_pybind_research_v0.6.1_smoke_results.zip %*
set "RUN_RC=%ERRORLEVEL%"
pause
exit /b %RUN_RC%
