@echo off
setlocal
cd /d "%~dp0"
set "PRESET=%~2"
if "%PRESET%"=="" set "PRESET=basic"
call run_all_blind.cmd "%~1" "%PRESET%" confirmatory
set "RC=%ERRORLEVEL%"
if "%RC%"=="1" exit /b 1
call run_40_reveal.cmd || exit /b 1
exit /b %RC%
