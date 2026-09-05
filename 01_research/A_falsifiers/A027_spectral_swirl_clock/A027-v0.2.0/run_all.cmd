@echo off
setlocal
cd /d "%~dp0"
set CAMPAIGN=%~1
if "%CAMPAIGN%"=="" set CAMPAIGN=campaigns
set OUTDIR=%~2
if "%OUTDIR%"=="" set OUTDIR=outputs_blind

echo ============================================================
echo SST v-arrow Spectral Blind Falsifier v0.2.0
echo Recursive campaign root: %CAMPAIGN%
echo Output: %OUTDIR%
echo Demo/synthetic data are excluded from this blind run.
echo ============================================================

call run_install.cmd || exit /b 1
call .venv\Scripts\activate.bat
python -m sst_v_arrow_falsifier audit --root . || exit /b 1
pytest -q || exit /b 1
python -m sst_v_arrow_falsifier scan "%CAMPAIGN%" "%OUTDIR%" || exit /b 1
call run_blind.cmd "%CAMPAIGN%" "%OUTDIR%" || exit /b 1

echo.
echo ============================================================
echo BLIND PHASE COMPLETE AND HASH-LOCKED.
echo Inspect:
echo   %OUTDIR%\campaign_scan\campaign_scan.csv
echo   %OUTDIR%\blind_results.json
echo   %OUTDIR%\blind_lock.json
echo Then, and only then: run_unblind.cmd "%OUTDIR%"
echo ============================================================
endlocal
