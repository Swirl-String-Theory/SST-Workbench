@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
set "BACKEND=%~2"
if "%BACKEND%"=="" set "BACKEND=auto"
if not exist .venv\Scripts\python.exe call run_install.cmd
if errorlevel 1 exit /b 1
echo ============================================================
echo KJ-SST EXTENDED RESOLUTION-LADDER CAMPAIGN
echo Dataset: %DATASET%
echo Backend: %BACKEND%
echo ============================================================
.venv\Scripts\python.exe run_pipeline.py --profile extended --dataset "%DATASET%" --backend %BACKEND%
exit /b %errorlevel%
