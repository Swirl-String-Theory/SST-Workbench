@echo off
setlocal
cd /d "%~dp0"
call _common.cmd || exit /b 1
if not exist "blind_catalog\pairs_public.csv" call run_12_prepare_relaxed_control.cmd || exit /b 1
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TS=%%i
set "OUT=outputs\blind_relaxed_control_%TS%"
"%PY%" -m sst_fourier_ideal_falsifier.cli run --project-root . --catalog blind_catalog --config config\preset_relaxed_control.json --out "%OUT%"
if errorlevel 1 exit /b 1
echo [SST-FVI] BLIND + SEALED: %OUT%
exit /b 0
