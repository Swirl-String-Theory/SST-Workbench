@echo off
setlocal
cd /d "%~dp0"
python bootstrap_upstream.py || exit /b 1
set "INSTANCE=%CD%\upstream_runtime\A069_3D_SwirlClock_Emergence\A069-v0.5.0"
set "KIND=B"
if not "%~1"=="" set "KIND=%~1"
set "GRID=32"
if not "%~2"=="" set "GRID=%~2"
set "STEPS=8"
if not "%~3"=="" set "STEPS=%~3"
python run_v061.py --v05-instance "%INSTANCE%" --kind %KIND% --n %GRID% --steps %STEPS% --output "results\%KIND%_N%GRID%_v061_local.json"
endlocal
