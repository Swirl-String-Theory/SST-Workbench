@echo off
setlocal EnableExtensions
call "%~dp0_paths.cmd"
cd /d "%ROOT%"
if not exist "%PY%" (echo [ERROR] Run run_00_install.cmd first.& exit /b 1)
if not exist "%SST_KNOTS_DIR%" (echo [ERROR] Knot directory not found: %SST_KNOTS_DIR%& exit /b 1)
for /f %%I in ('"%PY%" -c "from datetime import datetime;print(datetime.now().strftime('%%Y%%m%%d_%%H%%M%%S'))"') do set TS=%%I
set "OUT=%ROOT%outputs_extended_%TS%"
echo [DFC] Running EXTENDED all-knot native campaign with %SST_NATIVE_THREADS% threads...
"%PY%" run_knot_campaign.py --knots-dir "%SST_KNOTS_DIR%" --config configs\knot_extended_v0.2.0.json --out "%OUT%" --threads %SST_NATIVE_THREADS% --require-native
set RC=%ERRORLEVEL%
echo [DFC] EXTENDED output: %OUT%
exit /b %RC%
