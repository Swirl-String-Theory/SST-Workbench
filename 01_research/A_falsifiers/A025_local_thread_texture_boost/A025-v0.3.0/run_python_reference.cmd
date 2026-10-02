@echo off
setlocal
cd /d "%~dp0"
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
if not exist ".venv\Scripts\python.exe" call run_install.cmd
if errorlevel 1 exit /b %errorlevel%
set SST_FORCE_PYTHON=1
.venv\Scripts\python.exe run_campaign.py --config config\quick.json --dataset "%DATASET%" --force-python
exit /b %errorlevel%
