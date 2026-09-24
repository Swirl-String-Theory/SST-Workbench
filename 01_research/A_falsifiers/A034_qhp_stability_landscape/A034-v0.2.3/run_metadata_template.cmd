@echo off
setlocal
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\qhp"
call .venv\Scripts\activate.bat
python -m sst_qhp_falsifier.cli metadata-template "%DATASET%"
