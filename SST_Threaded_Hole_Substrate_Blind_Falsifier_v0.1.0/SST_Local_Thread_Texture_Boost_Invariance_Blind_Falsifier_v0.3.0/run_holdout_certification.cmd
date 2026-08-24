@echo off
setlocal
cd /d "%~dp0"
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
if not exist ".venv\Scripts\python.exe" call run_install.cmd
if errorlevel 1 exit /b %errorlevel%
.venv\Scripts\python.exe run_holdout_certification.py --config config\holdout.json --dataset "%DATASET%"
exit /b %errorlevel%
