@echo off
setlocal
cd /d "%~dp0"
set "V030=%~1"
if "%V030%"=="" set "V030=..\A056-v0.3.0\data\runtime_e010_filament"
echo [A056-v0.4.0] DEVELOPMENT-ONLY reanalysis of v0.3.0 data. This cannot close a v0.4.0 gate.
call run_python.cmd tools\diagnose_spectral_v2.py --input-dir "%V030%" --config configs\e010_real_score.json --output A056_V030_DEVELOPMENT_REANALYSIS_V040.json
exit /b %ERRORLEVEL%
