@echo off
setlocal
cd /d "%~dp0"
set "OUT=%~1"
if "%OUT%"=="" set "OUT=SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.4.0-outputs"
python reveal\interpret.py "%OUT%" || exit /b 1
endlocal
