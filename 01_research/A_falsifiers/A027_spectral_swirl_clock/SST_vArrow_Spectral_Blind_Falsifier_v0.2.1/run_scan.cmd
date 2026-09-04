@echo off
setlocal EnableExtensions
cd /d "%~dp0" || exit /b 1

set "CAMPAIGN=%~1"
if not defined CAMPAIGN set "CAMPAIGN=campaigns"
set "OUTDIR=%~2"
if not defined OUTDIR set "OUTDIR=outputs_scan"

call "%~dp0run_install.cmd"
if errorlevel 1 endlocal & exit /b 1

set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" (
    echo ERROR: Python not found after installation: "%PY%"
    endlocal & exit /b 1
)

echo.
echo [scan] Recursive root: "%CAMPAIGN%"
echo [scan] Output:         "%OUTDIR%"
"%PY%" -m sst_v_arrow_falsifier scan "%CAMPAIGN%" "%OUTDIR%"
if errorlevel 1 endlocal & exit /b 1

echo.
echo Recursive scan complete: %OUTDIR%\campaign_scan\campaign_scan.csv
endlocal & exit /b 0
