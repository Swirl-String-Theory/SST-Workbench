@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
set CFG=%~2
if "%CFG%"=="" set CFG=config\basic.json
set OUT=%~3
if "%OUT%"=="" (
  for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TS=%%i
  set OUT=outputs\basic_%TS%
)
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
"%PY%" -m sst_wp.campaign "%DATA%" --config "%CFG%" --out "%OUT%" || exit /b 1
echo %OUT%> outputs\LAST_OUT.txt
popd
endlocal
