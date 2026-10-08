@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=BLIND"
echo A059 v0.2.0 - self-contained dynamic Rosetta mega falsifier
echo Mode: %MODE%
call run_python.cmd -m mega.orchestrator %MODE%
exit /b %ERRORLEVEL%
