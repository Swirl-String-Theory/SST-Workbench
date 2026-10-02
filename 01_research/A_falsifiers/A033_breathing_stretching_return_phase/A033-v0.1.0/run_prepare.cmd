@echo off
setlocal
set "DATASET=%~1"
set "WORK=%~2"
set "CFG=%~3"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
if "%WORK%"=="" set "WORK=outputs\basic"
if "%CFG%"=="" set "CFG=config\basic.json"
call .venv\Scripts\activate.bat
python -m sst_bsrp_falsifier.cli prepare "%DATASET%" "%WORK%" "%CFG%"
