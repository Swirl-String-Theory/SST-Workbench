@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: run_blind.cmd ^<campaign_dir^> [outdir]
  exit /b 2
)
set CAMPAIGN=%~1
if "%~2"=="" (set OUTDIR=outputs_blind) else (set OUTDIR=%~2)
call .venv\Scripts\activate.bat
python -m sst_v_arrow_falsifier blind "%CAMPAIGN%" "%OUTDIR%" --config config\default.json || exit /b 1
python -m sst_v_arrow_falsifier freeze "%OUTDIR%" || exit /b 1
python -m sst_v_arrow_falsifier plot "%OUTDIR%"
echo.
echo BLIND RESULTS FROZEN. Do not edit %OUTDIR%\blind_results.json before unblinding.
endlocal
