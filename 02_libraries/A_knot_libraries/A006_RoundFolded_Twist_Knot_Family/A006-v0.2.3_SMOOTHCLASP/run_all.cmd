@echo off
setlocal
cd /d "%~dp0"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=BASIC"
set "PYTHON=python"
where python >nul 2>&1 || set "PYTHON=py -3"
%PYTHON% -m pytest tests -q
if errorlevel 1 exit /b 1
%PYTHON% src\build.py "%MODE%"
if errorlevel 1 exit /b 1
echo Static build done. Open KnotPlot LOAD scripts; no go or relaxation was run automatically.
endlocal
