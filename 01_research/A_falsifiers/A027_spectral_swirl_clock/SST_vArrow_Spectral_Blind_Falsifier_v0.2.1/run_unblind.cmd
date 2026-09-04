@echo off
setlocal EnableExtensions
cd /d "%~dp0" || exit /b 1
set "OUTDIR=%~1"
if not defined OUTDIR set "OUTDIR=outputs_blind"
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" (
    echo ERROR: .venv is missing. Run run_install.cmd first.
    endlocal & exit /b 1
)
"%PY%" -m sst_v_arrow_falsifier unblind "%OUTDIR%" --target sealed\unblind_target.json --config config\default.json
if errorlevel 1 endlocal & exit /b 1
endlocal & exit /b 0
