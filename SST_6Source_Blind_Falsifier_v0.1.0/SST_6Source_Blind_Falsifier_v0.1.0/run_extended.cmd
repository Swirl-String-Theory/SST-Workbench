@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "DATASET=%~1"
if not defined DATASET if exist "..\..\KnotPlot\knots\final" set "DATASET=..\..\KnotPlot\knots\final"
if not defined DATASET set "DATASET=data\sample_knots"
if not exist ".venv\Scripts\python.exe" (
  echo Missing .venv. Run run_all.cmd once, or run_install.cmd.
  exit /b 2
)
".venv\Scripts\python.exe" run_campaign.py --config config\campaign_extended.json --dataset "%DATASET%" --require-native
exit /b %errorlevel%
