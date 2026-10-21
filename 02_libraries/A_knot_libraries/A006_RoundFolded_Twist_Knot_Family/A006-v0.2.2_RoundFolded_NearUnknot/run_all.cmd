KnotPlot.lnk@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (set MODE=BASIC) else (set MODE=%~1)
py -3 -m pytest -q tests
if errorlevel 1 exit /b 1
py -3 src\build.py %MODE%
if errorlevel 1 exit /b 1
py -3 src\preview.py
if errorlevel 1 exit /b 1
echo [STATIC BUILD FINISHED] Check LATEST_BUILD.json and per-case REPORT.json
endlocal