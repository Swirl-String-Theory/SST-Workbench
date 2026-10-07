@echo off
setlocal
cd /d "%~dp0"
set PRESET=%~1
if "%PRESET%"=="" set PRESET=full
set WB=%~2
if "%WB%"=="" set WB=C:\workspace\projects\SST-Workbench
.venv\Scripts\python.exe -m a055_spectrum.cli a054-preflight --config configs/%PRESET%.json --workbench-root "%WB%" --ensure
