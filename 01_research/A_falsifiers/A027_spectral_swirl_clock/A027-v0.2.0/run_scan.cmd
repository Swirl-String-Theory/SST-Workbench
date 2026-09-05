@echo off
setlocal
cd /d "%~dp0"
set CAMPAIGN=%~1
if "%CAMPAIGN%"=="" set CAMPAIGN=campaigns
set OUTDIR=%~2
if "%OUTDIR%"=="" set OUTDIR=outputs_scan
call run_install.cmd || exit /b 1
call .venv\Scripts\activate.bat
python -m sst_v_arrow_falsifier scan "%CAMPAIGN%" "%OUTDIR%" || exit /b 1
echo.
echo Recursive scan complete: %OUTDIR%\campaign_scan\campaign_scan.csv
endlocal
