@echo off
setlocal
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
set "OUT=%~2"
if "%OUT%"=="" set "OUT=..\..\KnotPlot\qhp_full_grid"
call .venv\Scripts\activate.bat
python -m qhp_sweep.generate "%DATASET%" --out "%OUT%" --clean-output --config config\full_grid.json
if errorlevel 1 exit /b 1
python -m qhp_sweep.audit "%OUT%"
endlocal
