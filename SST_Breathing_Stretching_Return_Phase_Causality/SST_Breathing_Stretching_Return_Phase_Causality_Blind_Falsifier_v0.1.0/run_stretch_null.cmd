@echo off
setlocal
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
set OMP_NUM_THREADS=%NUMBER_OF_PROCESSORS%
call .venv\Scripts\activate.bat
python -m sst_bsrp_falsifier.cli prepare "%DATASET%" outputs\extended_fixedcore config\fixedcore_extended.json || goto :fail
python -m sst_bsrp_falsifier.cli run outputs\extended_fixedcore config\fixedcore_extended.json || goto :fail
python -m sst_bsrp_falsifier.cli analyze outputs\extended_fixedcore config\fixedcore_extended.json || goto :fail
python -m sst_bsrp_falsifier.cli stretch-compare outputs\extended outputs\extended_fixedcore outputs\stretch_mediation_summary.json || goto :fail
echo Stretch mediation summary: outputs\stretch_mediation_summary.json
exit /b 0
:fail
exit /b 1
