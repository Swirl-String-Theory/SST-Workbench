@echo off
setlocal
cd /d "%~dp0"
set PRESET=%~1
if "%PRESET%"=="" set PRESET=quick
set WB=%~2
if "%WB%"=="" set WB=C:\workspace\projects\SST-Workbench
.venv\Scripts\python.exe -m a055_spectrum.cli blind --config configs/%PRESET%.json --workbench-root "%WB%" --overwrite
