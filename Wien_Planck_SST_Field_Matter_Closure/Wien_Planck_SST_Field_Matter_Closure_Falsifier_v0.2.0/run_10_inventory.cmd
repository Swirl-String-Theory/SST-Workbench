@echo off
setlocal
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
call .venv\Scripts\activate.bat || exit /b 1
python -m sst_wp.inventory "%DATA%" --out outputs\dataset_inventory.json --n 96 || exit /b 1
endlocal
