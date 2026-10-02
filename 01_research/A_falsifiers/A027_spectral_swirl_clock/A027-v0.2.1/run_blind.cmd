@echo off
setlocal EnableExtensions
cd /d "%~dp0" || exit /b 1
set "CAMPAIGN=%~1"
if not defined CAMPAIGN set "CAMPAIGN=campaigns"
set "OUTDIR=%~2"
if not defined OUTDIR set "OUTDIR=outputs_blind"
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" (
    echo ERROR: .venv is missing. Run run_install.cmd first.
    endlocal & exit /b 1
)
"%PY%" -m sst_v_arrow_falsifier blind "%CAMPAIGN%" "%OUTDIR%" --config config\default.json --recursive
if errorlevel 1 endlocal & exit /b 1
"%PY%" -m sst_v_arrow_falsifier freeze "%OUTDIR%"
if errorlevel 1 endlocal & exit /b 1
"%PY%" -m sst_v_arrow_falsifier plot "%OUTDIR%"
if errorlevel 1 endlocal & exit /b 1
echo.
echo BLIND RESULTS FROZEN. Do not edit %OUTDIR%\blind_results.json before unblinding.
endlocal & exit /b 0
