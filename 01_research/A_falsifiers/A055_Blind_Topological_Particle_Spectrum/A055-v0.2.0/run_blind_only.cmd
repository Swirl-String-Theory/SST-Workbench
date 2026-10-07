@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set PRESET=%~1
if "%PRESET%"=="" set PRESET=full
set WB=%~2
if "%WB%"=="" set WB=C:\workspace\projects\SST-Workbench
call run_00_install.cmd || exit /b 1
call run_05_build_cpp.cmd || exit /b 1
.venv\Scripts\python.exe -m a055_spectrum.cli selftest || exit /b 1
call run_20_blind.cmd %PRESET% "%WB%" || exit /b 1
call run_30_seal.cmd %PRESET% || exit /b 1
echo BLIND campaign sealed. Reveal NOT run.
