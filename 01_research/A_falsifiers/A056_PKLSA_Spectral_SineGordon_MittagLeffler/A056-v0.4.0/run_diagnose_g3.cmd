@echo off
setlocal
cd /d "%~dp0"
set "INPUT=%~1"
if "%INPUT%"=="" set "INPUT=data\runtime_e010_filament_v040_m4"
call run_python.cmd tools\diagnose_g3.py --input-dir "%INPUT%" --config configs\e010_real_score.json --output A056_G3_DIAGNOSTICS_READONLY.json --csv-output A056_G3_DIAGNOSTICS_READONLY.csv
exit /b %ERRORLEVEL%
