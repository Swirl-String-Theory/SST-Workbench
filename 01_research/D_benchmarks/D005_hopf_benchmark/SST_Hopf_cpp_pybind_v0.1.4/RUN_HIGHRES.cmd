@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call "cmd\00_SETUP_VENV.cmd"
if errorlevel 1 exit /b 1
call "cmd\01_BUILD_CPP.cmd"
if errorlevel 1 exit /b 1
call "cmd\04_RUN_HIGHRES_CPP.cmd"
exit /b %errorlevel%
