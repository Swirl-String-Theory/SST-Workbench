@echo off
setlocal
cd /d "%~dp0"
set "INPUT=%~1"
if "%INPUT%"=="" set "INPUT=data\runtime_e010_filament_v040_m4"
call run_python.cmd tools\diagnose_spectral_v2.py --input-dir "%INPUT%" --config configs\e010_real_score.json --output A056_G2_V040_DIAGNOSTICS_READONLY.json
exit /b %ERRORLEVEL%
