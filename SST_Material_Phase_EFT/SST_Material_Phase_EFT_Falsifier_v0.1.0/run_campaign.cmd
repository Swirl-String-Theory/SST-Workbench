@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" goto usage
if "%~2"=="" goto usage
set "CFG=%~1"
set "OUT=%~2"
set "DATASET=%~3"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
if not exist .venv call run_setup.cmd
call .venv\Scripts\activate.bat
python -m sst_eft_falsifier.campaign --config "%CFG%" --dataset "%DATASET%" --outdir "%OUT%"
set RC=%ERRORLEVEL%
endlocal & exit /b %RC%
:usage
echo Usage: run_campaign.cmd ^<config.json^> ^<outdir^> [dataset]
exit /b 2
