@echo off
setlocal
cd /d "%~dp0"
call _common.cmd || exit /b 1
if not exist "blind_catalog\pairs_public.csv" call run_10_prepare_torus.cmd || exit /b 1
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TS=%%i
set "OUT=outputs\blind_torus_%TS%"
"%PY%" -m sst_fourier_ideal_falsifier.cli run --project-root . --catalog blind_catalog --config config\preset_torus.json --out "%OUT%"
if errorlevel 1 exit /b 1
echo [SST-FVI] BLIND + SEALED: %OUT%
echo [SST-FVI] Do not alter files before reveal.
exit /b 0
