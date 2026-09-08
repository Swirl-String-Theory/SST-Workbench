@echo off
setlocal EnableExtensions
call "%~dp0_paths.cmd"
cd /d "%ROOT%"
if not exist "%PY%" (echo [ERROR] Run run_00_install.cmd first.& exit /b 1)
if not exist "%SST_KNOTS_DIR%" (echo [ERROR] Knot directory not found: %SST_KNOTS_DIR%& exit /b 1)
for /f %%I in ('"%PY%" -c "from datetime import datetime;print(datetime.now().strftime('%%Y%%m%%d_%%H%%M%%S'))"') do set TS=%%I
set "OUT=%ROOT%outputs_extended_%TS%"
"%PY%" run_campaign.py --knots-dir "%SST_KNOTS_DIR%" --config configs\extended_v0.1.0.json --out "%OUT%" --threads %SST_NATIVE_THREADS% --require-native
set RC=%ERRORLEVEL%
echo [H-SST] EXTENDED output: %OUT%
exit /b %RC%
