@echo off
setlocal
set "WB=C:\workspace\projects\SST-Workbench"
py -3 "%~dp0install_additive.py" --workbench "%WB%" %*
if errorlevel 1 exit /b 1
py -3 "%~dp0verify_dataset.py" --dataset "%WB%\03_data\A_knots\04_knotplot\PKLSA_KnotPlot_Native_Census_v0.1.2"
exit /b %errorlevel%
