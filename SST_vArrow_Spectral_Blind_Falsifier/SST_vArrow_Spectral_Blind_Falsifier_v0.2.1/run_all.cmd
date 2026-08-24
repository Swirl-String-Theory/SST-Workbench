@echo off
setlocal EnableExtensions
cd /d "%~dp0" || exit /b 1
set "CAMPAIGN=%~1"
if not defined CAMPAIGN set "CAMPAIGN=campaigns"
set "OUTDIR=%~2"
if not defined OUTDIR set "OUTDIR=outputs_blind"

set "PY=%~dp0.venv\Scripts\python.exe"
set "PYTEST=%~dp0.venv\Scripts\pytest.exe"

echo ============================================================
echo SST v-arrow Spectral Blind Falsifier v0.2.1
echo Recursive campaign root: %CAMPAIGN%
echo Output: %OUTDIR%
echo Demo/synthetic data are excluded from this blind run.
echo ============================================================

call "%~dp0run_install.cmd"
if errorlevel 1 endlocal & exit /b 1

"%PY%" -m sst_v_arrow_falsifier audit --root .
if errorlevel 1 endlocal & exit /b 1
"%PYTEST%" -q
if errorlevel 1 endlocal & exit /b 1
"%PY%" -m sst_v_arrow_falsifier scan "%CAMPAIGN%" "%OUTDIR%"
if errorlevel 1 endlocal & exit /b 1
call "%~dp0run_blind.cmd" "%CAMPAIGN%" "%OUTDIR%"
if errorlevel 1 endlocal & exit /b 1

echo.
echo ============================================================
echo BLIND PHASE COMPLETE AND HASH-LOCKED.
echo Inspect:
echo   %OUTDIR%\campaign_scan\campaign_scan.csv
echo   %OUTDIR%\blind_results.json
echo   %OUTDIR%\blind_lock.json
echo Then, and only then: run_unblind.cmd "%OUTDIR%"
echo ============================================================
endlocal & exit /b 0
