@echo off
setlocal
cd /d "%~dp0"
set CAMPAIGN=%~1
if "%CAMPAIGN%"=="" set CAMPAIGN=campaigns
set OUTDIR=%~2
if "%OUTDIR%"=="" set OUTDIR=outputs_blind
call .venv\Scripts\activate.bat
python -m sst_v_arrow_falsifier blind "%CAMPAIGN%" "%OUTDIR%" --config config\default.json --recursive || exit /b 1
python -m sst_v_arrow_falsifier freeze "%OUTDIR%" || exit /b 1
python -m sst_v_arrow_falsifier plot "%OUTDIR%"
echo.
echo BLIND RESULTS FROZEN. Do not edit %OUTDIR%\blind_results.json before unblinding.
endlocal
